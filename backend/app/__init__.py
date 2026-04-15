"""
MiroFish Backend - Flask Application Factory
"""

import os
import warnings

# Suppress multiprocessing resource_tracker warnings (from third-party libraries like transformers)
# Needs to be set before all other imports
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger
from .utils.llm_client import install_openai_cost_tracker


def create_app(config_class=Config):
    """Flask application factory function"""
    # Install LLM cost tracker as early as possible so every downstream
    # openai.*.completions.create in this process is counted.
    install_openai_cost_tracker()

    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class)

    # Initialize Sentry (must be before other imports)
    if Config.SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        sentry_sdk.init(
            dsn=Config.SENTRY_DSN,
            integrations=[FlaskIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            send_default_pii=False,
        )

    # Set JSON encoding: ensure non-ASCII characters display directly (instead of \uXXXX format)
    # Flask >= 2.3 uses app.json.ensure_ascii, older versions use JSON_AS_ASCII config
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    # Set up logging
    logger = setup_logger('mirofish')

    # Only print startup info in the reloader subprocess (avoid printing twice in debug mode)
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend starting...")
        logger.info("=" * 50)

    # Enable CORS
    origins = [o.strip() for o in Config.ALLOWED_ORIGINS.split(',') if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins, "supports_credentials": True}})

    # Rate limiting
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    def _rate_limit_key():
        from flask import g
        user = getattr(g, 'current_user', None)
        if user and hasattr(user, 'id'):
            return f"user:{user.id}"
        return get_remote_address()

    # Use Redis if available, fall back to in-memory
    _storage_uri = Config.REDIS_URL
    try:
        import redis as _redis
        _r = _redis.from_url(Config.REDIS_URL, socket_connect_timeout=2)
        _r.ping()
    except Exception:
        _storage_uri = "memory://"
        logger.warning("Redis unavailable — rate limiter using in-memory storage")

    limiter = Limiter(
        app=app,
        key_func=_rate_limit_key,
        storage_uri=_storage_uri,
        default_limits=["100 per minute"],
        strategy="fixed-window",
    )
    app.limiter = limiter

    # Register simulation process cleanup function (ensure all simulation processes are terminated when server shuts down)
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Registered simulation process cleanup function")

    # HTTPS enforcement + safe request logging
    @app.before_request
    def before_request_handler():
        import uuid
        from flask import g
        g.request_id = str(uuid.uuid4())[:8]
        logger = get_logger('mirofish.request')
        # HTTPS enforcement
        if not app.debug and request.path != '/health':
            forwarded_proto = request.headers.get('X-Forwarded-Proto', 'https')
            if forwarded_proto == 'http':
                from flask import redirect
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
        # Safe request logging (no body — avoids PII leaks)
        logger.debug(f"Request: {request.method} {request.path}")

    @app.after_request
    def add_security_headers(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"Response: {response.status_code}")
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['X-XSS-Protection'] = '0'
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: blob:; "
                "connect-src 'self'"
            )
        return response

    # Initialize database tables (auto-create if they don't exist)
    try:
        from .db import Base, engine
        from .models import db_models as _db_models  # noqa: ensure all models are registered
        Base.metadata.create_all(bind=engine)

        # Add missing columns to existing tables (lightweight migration)
        from sqlalchemy import text, inspect
        with engine.connect() as conn:
            inspector = inspect(engine)
            existing_cols = {c['name'] for c in inspector.get_columns('users')}
            new_cols = {
                'dodo_customer_id': 'VARCHAR(255)',
                'dodo_subscription_id': 'VARCHAR(255)',
                'subscription_status': 'VARCHAR(50)',
                'current_period_end': 'TIMESTAMP WITH TIME ZONE',
            }
            for col_name, col_type in new_cols.items():
                if col_name not in existing_cols:
                    conn.execute(text(f'ALTER TABLE users ADD COLUMN {col_name} {col_type}'))
                    conn.commit()
                    if should_log_startup:
                        logger.info(f"Added missing column: users.{col_name}")

        # Add service_origin to tasks table if missing
            if 'tasks' in [t for t in inspector.get_table_names()]:
                task_cols = {c['name'] for c in inspector.get_columns('tasks')}
                if 'service_origin' not in task_cols:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN service_origin VARCHAR(50)"))
                    conn.commit()
                    if should_log_startup:
                        logger.info("Added missing column: tasks.service_origin")

        if should_log_startup:
            logger.info("Database tables initialized")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")

    # Recover stale tasks from previous server crashes
    try:
        from .db import get_db
        with get_db() as session:
            from .repositories.task_repo import TaskRepository
            count = TaskRepository(session).recover_stale()
            if count > 0 and should_log_startup:
                logger.info(f"Recovered {count} stale tasks from previous crash")
    except Exception as e:
        logger.warning(f"Task recovery skipped: {e}")

    # Recover simulations stuck in 'running' state from previous crash
    try:
        from .db import get_db
        with get_db() as session:
            from .repositories.simulation_repo import SimulationRepository
            sim_repo = SimulationRepository(session)
            stuck = sim_repo.find_by_status('running')
            for sim in stuck:
                sim.status = 'interrupted'
                if should_log_startup:
                    logger.warning(f"Recovered stuck simulation: {sim.id} (was 'running', now 'interrupted')")
            if stuck:
                session.commit()
                if should_log_startup:
                    logger.info(f"Recovered {len(stuck)} stuck simulations from previous crash")
    except Exception as e:
        logger.warning(f"Simulation recovery skipped: {e}")

    # Register error handlers
    from .middleware.errors import register_error_handlers
    register_error_handlers(app)

    # API documentation
    from flasgger import Swagger
    swagger_config = {
        "headers": [],
        "specs": [{
            "endpoint": "apispec",
            "route": "/api/docs/apispec.json",
        }],
        "static_url_path": "/api/docs/static",
        "swagger_ui": True,
        "specs_route": "/api/docs/",
    }
    swagger_template = {
        "info": {
            "title": "MiroFish API",
            "description": "AI-Powered Swarm Intelligence Engine API",
            "version": "1.0.0",
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Bearer token. Format: 'Bearer {token}'"
            }
        },
        "security": [{"Bearer": []}],
    }
    Swagger(app, config=swagger_config, template=swagger_template)

    # Register blueprints
    from .api import graph_bp, simulation_bp, report_bp, auth_bp, billing_bp, predict_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(billing_bp, url_prefix='/api/billing')
    app.register_blueprint(predict_bp, url_prefix='/api/predict')

    from .api.crawl_import import crawl_import_bp
    app.register_blueprint(crawl_import_bp, url_prefix='/api/predict')

    # Endpoint-specific rate limits
    auth_limits = {
        'auth.login': '5 per minute',
        'auth.signup': '5 per minute',
        'auth.refresh': '10 per minute',
    }
    for endpoint, limit_str in auth_limits.items():
        view_fn = app.view_functions.get(endpoint)
        if view_fn:
            app.view_functions[endpoint] = limiter.limit(limit_str, key_func=get_remote_address)(view_fn)

    upload_limits = {'graph.upload_file': '10 per hour'}
    for endpoint, limit_str in upload_limits.items():
        view_fn = app.view_functions.get(endpoint)
        if view_fn:
            app.view_functions[endpoint] = limiter.limit(limit_str)(view_fn)

    llm_limits = {
        'graph.generate_ontology': '20 per hour',
        'graph.build_graph': '20 per hour',
        'simulation.start_simulation': '20 per hour',
    }
    for endpoint, limit_str in llm_limits.items():
        view_fn = app.view_functions.get(endpoint)
        if view_fn:
            app.view_functions[endpoint] = limiter.limit(limit_str)(view_fn)

    # Health check
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}

    from flask import send_from_directory, jsonify

    # Serve landing page at /
    landing_dir = os.path.join(os.path.dirname(__file__), '../../landing')
    if os.path.isdir(landing_dir):
        @app.route('/')
        def serve_landing():
            return send_from_directory(landing_dir, 'index.html')

        @app.route('/landing/<path:path>')
        def serve_landing_assets(path):
            return send_from_directory(landing_dir, path)

        if should_log_startup:
            logger.info(f"Serving landing page from {landing_dir}")

    # Serve static assets (images, videos used by landing page)
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../static'))
    if os.path.isdir(static_dir):
        @app.route('/static/<path:path>')
        def serve_static_assets(path):
            try:
                return send_from_directory(static_dir, path)
            except Exception as e:
                logger.error(f"Static file error: {path} from {static_dir}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return jsonify({"error": str(e)}), 404
    else:
        logger.warning(f"Static dir not found: {os.path.join(os.path.dirname(__file__), '../../static')}")

    # Serve frontend SPA for all other routes
    frontend_dist = os.path.join(os.path.dirname(__file__), '../../frontend/dist')
    if os.path.isdir(frontend_dist):
        @app.route('/<path:path>')
        def serve_frontend(path):
            # Don't handle API, landing, static, or health routes
            if path.startswith(('api/', 'landing/', 'static/', 'health')):
                return
            file_path = os.path.join(frontend_dist, path)
            if os.path.isfile(file_path):
                return send_from_directory(frontend_dist, path)
            return send_from_directory(frontend_dist, 'index.html')

        if should_log_startup:
            logger.info(f"Serving frontend from {frontend_dist}")

    if should_log_startup:
        logger.info("MiroFish Backend startup complete")

    return app
