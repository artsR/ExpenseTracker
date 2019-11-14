from config import Config
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# from flask_bootstrap import Bootstrap
from flask_admin import Admin



db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
login.login_message_category = 'danger'
# bootstrap = Bootstrap()
admin = Admin()


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    # bootstrap.init_app(app)
    admin.init_app(app)


    from eTracker.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from eTracker.main import bp as main_bp
    app.register_blueprint(main_bp)
    from eTracker.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app


from eTracker import models

from flask_admin.contrib.sqla import ModelView
admin.add_view(ModelView(models.User, db.session))
admin.add_view(ModelView(models.Expense, db.session))
admin.add_view(ModelView(models.Currency, db.session))
admin.add_view(ModelView(models.CurrencyOfficialAbbr, db.session))
