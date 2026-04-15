"""
Configuration Management
Loads configuration from the .env file in the project root directory
"""

import os
from dotenv import load_dotenv

# Load .env file from the project root directory
# Path: MiroFish/.env (relative to backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    # If no .env in root directory, try loading environment variables (for production)
    load_dotenv(override=True)


class Config:
    """Flask configuration class"""

    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mirofish-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # JSON configuration - disable ASCII escaping to display non-ASCII characters directly (instead of \uXXXX format)
    JSON_AS_ASCII = False

    # Admin access. Comma-separated list of emails that gate /api/admin/*.
    ADMIN_EMAILS = [
        e.strip().lower()
        for e in os.environ.get('ADMIN_EMAILS', 'ashish.dhiman@frozo.ai').split(',')
        if e.strip()
    ]

    # LLM configuration (unified OpenAI-compatible format)
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    # Cheap-tier model for bulk work (agent profile generation, simulation
    # actions, seed brief synthesis). Falls back to LLM_MODEL_NAME when unset.
    # Example (via OpenRouter): 'google/gemini-2.0-flash-001' or 'deepseek/deepseek-chat'.
    LLM_CHEAP_MODEL_NAME = os.environ.get('LLM_CHEAP_MODEL_NAME') or os.environ.get('LLM_MODEL_NAME', 'openai/gpt-4o-mini')

    # Graphiti knowledge-graph extraction. Uses the cheap tier by default so
    # graph-build calls flow through the same OpenRouter key. Flip this
    # (e.g. GRAPHITI_MODEL_NAME=openai/gpt-4o-mini) if a model misbehaves on
    # graphiti's JSON-schema prompts without changing the rest of the stack.
    GRAPHITI_MODEL_NAME = os.environ.get('GRAPHITI_MODEL_NAME') or LLM_CHEAP_MODEL_NAME

    # File upload configuration
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    # Text processing configuration
    DEFAULT_CHUNK_SIZE = 1500  # Larger chunks = fewer API calls, better context for Graphiti
    DEFAULT_CHUNK_OVERLAP = 100  # Default overlap size

    # OASIS simulation configuration
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '5'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    # How many agent profiles to generate per LLM call. 1 disables batching
    # (falls back to one call per entity). 8 is a good quality/throughput
    # balance; raise for cheap models, lower if truncation becomes common.
    OASIS_PROFILE_BATCH_SIZE = int(os.environ.get('OASIS_PROFILE_BATCH_SIZE', '8'))

    # OASIS platform available actions configuration
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Report Agent configuration
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/mirofish')

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '900'))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', '604800'))

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', '')

    # Dodo Payments
    DODO_API_KEY = os.environ.get('DODO_API_KEY', '')
    DODO_WEBHOOK_SECRET = os.environ.get('DODO_WEBHOOK_SECRET', '')
    DODO_STARTER_PRODUCT_ID = os.environ.get('DODO_STARTER_PRODUCT_ID', '')
    DODO_PRO_PRODUCT_ID = os.environ.get('DODO_PRO_PRODUCT_ID', '')
    DODO_ENVIRONMENT = os.environ.get('DODO_ENVIRONMENT', 'test_mode')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://frozo-mirofish-production.up.railway.app')

    # Resend (Email)
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    EMAIL_FROM = os.environ.get('EMAIL_FROM', 'Augur <noreply@augur.email>')

    # Graphiti / Neo4j (replaces Zep Cloud)
    NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password')

    # BettaFish Integration
    BETTAFISH_SERVICE_KEY = os.environ.get('BETTAFISH_SERVICE_KEY', '')

    # CORS
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000')

    # Redis (used for rate limiting and caching)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    # Sentry
    SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY is not configured")
        if cls.JWT_SECRET_KEY == 'dev-secret-change-in-production':
            import logging
            logging.getLogger('mirofish').warning("JWT_SECRET_KEY is using default dev value — set it in production!")
        return errors
