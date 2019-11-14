from flask import jsonify
from flask_login import current_user, login_required
from eTracker.api import bp
from eTracker.models import User, Expense, Currency



@bp.route('/expense', methods=['GET'])
@login_required
def get_expenses():
    pass
