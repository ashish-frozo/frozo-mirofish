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


def create_app(config_class=Config):
    """Flask application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

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
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register simulation process cleanup function (ensure all simulation processes are terminated when server shuts down)
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Registered simulation process cleanup function")

    # Request logging middleware
    @app.before_request
    def log_request():
        logger = get_logger('mirofish.request')
        logger.debug(f"Request: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"Request body: {request.get_json(silent=True)}")

    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"Response: {response.status_code}")
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

    # Register error handlers
    from .middleware.errors import register_error_handlers
    register_error_handlers(app)

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

    # Health check
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}

    from flask import send_from_directory

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
    static_dir = os.path.join(os.path.dirname(__file__), '../../static')
    if os.path.isdir(static_dir):
        @app.route('/static/<path:path>')
        def serve_static_assets(path):
            # Explicit MIME types for media files
            mimetype = None
            if path.endswith('.mp4'):
                mimetype = 'video/mp4'
            elif path.endswith('.webm'):
                mimetype = 'video/webm'
            return send_from_directory(static_dir, path, mimetype=mimetype)

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
