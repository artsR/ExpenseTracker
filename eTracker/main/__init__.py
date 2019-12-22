from flask import Blueprint



bp = Blueprint('main', __name__)


from eTracker.main import routes
