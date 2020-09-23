import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from config import Config
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect



db = SQLAlchemy()
migrate = Migrate()

login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
login.login_message_category = 'danger'

admin = Admin()
mail = Mail()

csrf = CSRFProtect()

def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    admin.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)


    from eTracker.auth import bp as auth_bp
    from eTracker.api import bp as api_bp
    from eTracker.main import bp as main_bp
    from eTracker.errors import bp as errors_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    csrf.exempt(api_bp)
    app.register_blueprint(errors_bp)

    if not app.debug:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=app.config['MAIL_DEFAULT_SENDER'],
                toaddrs=app.config['MAIL_ADMINS'],
                subject='eTRACKER Error',
                credentials=auth, secure=secure,
            )
            mail_handler.setLevel(logging.ERROR)
            logging.getLogger('werkzeug').addHandler(mail_handler)

        if app.config['LOG_TO_STDOUT'] is not None:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/eTracker.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('eTracker startup')

    return app


from eTracker import models

from flask_admin.contrib.sqla import ModelView
admin.add_view(ModelView(models.User, db.session))
admin.add_view(ModelView(models.Currency, db.session))
admin.add_view(ModelView(models.Wallet, db.session))
admin.add_view(ModelView(models.Subwallet, db.session))
admin.add_view(ModelView(models.Category, db.session))
admin.add_view(ModelView(models.Transaction, db.session))
