from flask import Blueprint



bp = Blueprint('auth', __name__)


from eTracker.auth import routes
