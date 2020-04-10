from flask import Blueprint



bp = Blueprint('errors', __name__)


from eTracker.errors import errors_handler
