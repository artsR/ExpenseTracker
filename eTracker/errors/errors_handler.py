from flask import render_template, request
from eTracker import db
from eTracker.errors import bp
from eTracker.api.errors_handler import error_response as api_error_response



def prefered_json_response():
    return (request.accept_mimetypes['application/json'] >=
            request.accept_mimetypes['text/html'])


@bp.app_errorhandler(400)
def internal_error(error):
    if prefered_json_response():
        return api_error_response(400)
    return (render_template('errors/error.html', error_message='Sorry! Bad Request',
                            error_number='400'), 400)


@bp.app_errorhandler(403)
def internal_error(error):
    if prefered_json_response():
        return api_error_response(403)
    return (render_template('errors/error.html', error_message='Sorry! Access denied',
                            error_number='403'), 403)


@bp.app_errorhandler(404)
def not_found_error(error):
    if prefered_json_response():
        return api_error_response(404)
    return (render_template('errors/error.html', error_message='Sorry! Page not found',
                            error_number='404'), 404)


@bp.app_errorhandler(405)
def internal_error(error):
    if prefered_json_response():
        return api_error_response(405)
    return (render_template('errors/error.html', error_message='Sorry! Method Not Allowed',
                            error_number='405'), 405)


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if prefered_json_response():
        return api_error_response(500)
    return (render_template('errors/error.html', error_message='Sorry! Temporary server error',
                            error_number='500'), 500)
