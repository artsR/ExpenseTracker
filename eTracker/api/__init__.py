from flask import Blueprint



bp = Blueprint('api', __name__)


from eTracker.api import routes, tokens, errors_handler
