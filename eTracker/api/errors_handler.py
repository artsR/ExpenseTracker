from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES



def error_response(status_code, msg=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if msg is not None:
        payload['message'] = msg
    response = jsonify(payload)
    response.status_code = status_code
    return response


def bad_request(msg):
    return error_response(400, msg)
