import os
from dotenv import load_dotenv



basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sometextsomenumber'

    # Database:
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        'sqlite:///' + os.path.join(basedir, 'exptracker.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads:
    ALLOWED_EXTENSIONS = set(['png', 'jpeg', 'jpg'])
    UPLOAD_FOLDER = os.path.join(basedir, 'eTracker/static/uploads')

    # Pagination:
    EXP_PER_PAGE = 5

    # Exchange Rate API:
    EX_RATE_API = os.environ.get('EX_RATE_API')

    # Recaptcha Keys:
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RC_PRIVATE_KEY')
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RC_PUBLIC_KEY')

    # Email Service:
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = 'pythonarts@op.pl'
    MAIL_ADMINS = ['pythonarts@op.pl']

    # API:
    JSON_SORT_KEYS = False
