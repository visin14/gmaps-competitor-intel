import os
from dotenv import load_dotenv

load_dotenv()

ON_VERCEL = bool(os.environ.get('VERCEL'))


def _database_uri():
    url = os.environ.get('DATABASE_URL')
    if url:
        # Some providers hand out postgres:// which SQLAlchemy 2 rejects
        return url.replace('postgres://', 'postgresql://', 1) if url.startswith('postgres://') else url
    # Vercel's filesystem is read-only except /tmp (data there is per-instance and temporary)
    return 'sqlite:////tmp/gmaps_intel.db' if ON_VERCEL else 'sqlite:///gmaps_intel.db'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-to-a-random-string')
    DATABASE_URI = _database_uri()
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GROK_API_KEY = os.environ.get('GROK_API_KEY', '')
    MEDIA_FOLDER = os.environ.get('MEDIA_FOLDER', 'static/media')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
