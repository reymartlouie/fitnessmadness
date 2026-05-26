import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    _secret = os.environ.get('SECRET_KEY')
    if not _secret:
        raise RuntimeError("SECRET_KEY environment variable is not set. Add it to your .env file.")
    SECRET_KEY = _secret
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'database', 'fitnessmadness.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes admin auto-logout
