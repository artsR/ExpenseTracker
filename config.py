import os



basedir = os.path.abspath(os.path.dirname(__file__))

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
