import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    _secret = os.environ.get('SECRET_KEY')
    if not _secret:
        raise RuntimeError("SECRET_KEY environment variable is not set. Add it to your .env file.")
    SECRET_KEY = _secret
    _db_url = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'database', 'fitnessmadness.db')
    # Resolve relative SQLite paths to absolute using the project root,
    # so the app works regardless of the working directory at launch time.
    if _db_url.startswith('sqlite:///') and not _db_url.startswith('sqlite:////'):
        _rel = _db_url[len('sqlite:///'):]
        if not os.path.isabs(_rel):
            _db_url = 'sqlite:///' + os.path.join(BASE_DIR, _rel)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes admin auto-logout
    GYM_NAME = os.environ.get('GYM_NAME', 'FitnessMadness')
