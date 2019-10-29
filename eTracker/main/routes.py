import os
from flask import render_template, redirect, url_for, flash, abort
from flask import current_app
from flask_login import current_user, login_required
from eTracker import db
from eTracker.models import User, Expense, Currency
from eTracker.main import bp
from eTracker.main.forms import AddExpenseForm, UploadForm, CurrencyForm, FiltersForm
from werkzeug.utils import secure_filename
import flask



@bp.route('/index')
@bp.route('/')
def index():

    return render_template('index.html')


@bp.route('/test')
def test():
    return render_template('test.html')


@bp.route('/expenses/')
@login_required
def expenses():
    return render_template('expenses.html')


@bp.route('/spendings', methods=['GET', 'POST'])
@login_required
def spendings():

    per_page = current_app.config['EXP_PER_PAGE']
    page = flask.request.args.get('page', 1, type=int)
    filters = {}

    form = FiltersForm()
    form.categories.choices = [ (col.category.lower(), col.category)
                        for col in current_user.get_categories().all() ]

    # if form.validate_on_submit():
    #     filters.update( {k: v for k, v in form.data.items() if v != None and k != 'csrf_token'} )
    #     flash(filters)

    expenses = current_user.spendings(filters).paginate(
                    page, per_page, 0)
    next_url = ( url_for('main.spendings', page=expenses.next_num)
        if expenses.has_next else None )
    prev_url = ( url_for('main.spendings', page=expenses.prev_num)
        if expenses.has_prev else None )

    return render_template('spendings.html', form=form, expenses=expenses,
                        next_url=next_url, prev_url=prev_url)


@bp.route('/expenses/edit_spending/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):

    expense = Expense.query.get_or_404(expense_id)

    if expense.user != current_user:
        abort(403)

    form = AddExpenseForm()

    if form.validate_on_submit():

        expense.expenseDate = form.expenseDate.data
        expense.product = form.product.data
        expense.category = form.category.data
        expense.freq = form.freq.data
        expense.quantity = form.quantity.data
        expense.price = form.price.data
        expense.currency = form.currency.data

        db.session.commit()
        flash('Your update has been saved.', 'success')

        return redirect(url_for('main.spendings'))

    # elif flask.request.method == 'GET':
    form.expenseDate.data = expense.expenseDate
    form.product.data = expense.product
    form.category.data = expense.category
    form.freq.data = expense.freq
    form.quantity.data = expense.quantity
    form.price.data = expense.price
    form.currency.data = expense.currency

    return render_template('add_expense.html', form=form, expense_id=expense_id)


@bp.route('/expenses/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):

    expense = Expense.query.get_or_404(expense_id)
    if expense.user != current_user:
        abort(403)
    db.session.delete(expense)
    db.session.commit()

    flash('Your expense has been deleted', 'success')

    return redirect(url_for('main.spendings'))


@bp.route('/expenses_add', methods=['GET', 'POST'])
@login_required
def expenses_add():

    form = AddExpenseForm()
    currency_grp = db.session.query(Currency.abbr).filter_by(user=current_user).all()
    form.currency.choices = [(curr[0], curr[0]) for curr in currency_grp]
    if form.validate_on_submit():
        expense = Expense(expenseDate=form.expenseDate.data, product=form.product.data,
                        category=form.category.data, freq=form.freq.data,
                        quantity=form.quantity.data, price=form.price.data,
                        currency=form.currency.data, user=current_user)
        db.session.add(expense)
        db.session.commit()
        flash('Expense added to you account.', 'success')
        return redirect(url_for('main.expenses_add'))

    return render_template('add_expense.html', form=form)


@bp.route('/upload')
@login_required
def upload():

    form = UploadForm()

    if flask.request.method == 'POST':
        if 'customFile' not in flask.request.files:
            flash("File wasn't uploaded correctly. Please try again", "danger")
            return redirect(url_for('main.upload'))

        f = flask.request.files['customFile']
        if f.filename == '':
            flash("File wasn't uploaded correctly. Please try again", "danger")
            return redirect(url_for('main.upload'))

        filename = secure_filename(f.filename)
        f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

        return redirect(url_for('main.receipt'))#, form=form))

    return render_template('upload.html', form=form)


@bp.route('/receipt', methods=['GET', 'POST'])
@login_required
def receipt():

    #form = receiptForm()

    if flask.request.method == 'POST':
        if 'customFile' not in flask.request.files:
            flash("File wasn't uploaded correctly. Please try again", "danger")
            return redirect(url_for('main.upload'))

        f = flask.request.files['customFile']
        if f.filename == '':
            flash("File wasn't uploaded correctly. Please try again", "danger")
            return redirect(url_for('main.upload'))

        filename = secure_filename(f.filename)
        f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

        return redirect(url_for('main.receipt'))#, form=form))

    return render_template('receipt.html')


@bp.route('/tools/')
def tools():
    return render_template('tools.html')


@bp.route('/tools/category/')
@login_required
def category():

    q = current_user.get_categories().all()
    categories = [(i, exp.category) for i, exp in enumerate(q, 1)]

    return render_template('tools_category.html', categories=categories)


@bp.route('/tools/currency/', methods=['GET', 'POST'])
@login_required
def currency():

    form = CurrencyForm()

    if form.validate_on_submit():
        currency = Currency(abbr=form.abbr.data.upper(), name=form.name.data,
                        user=current_user)
        db.session.add(currency)
        db.session.commit()
        flash('Currency was added into your account.', 'success')
        redirect(url_for('main.currency'))

    currs = Currency.query.filter_by(user = current_user).group_by(Currency.abbr).all()

    return render_template('tools_currency.html', currs=currs, form=form)


@bp.route('/tools/currency/delete/', methods=['POST'])
@login_required
def delete_currency():

    currency = Currency.query.get_or_404(flask.request.form['id'])
    if currency.user != current_user:
        abort(403)
    flash(flask.request.form)
    flash('Currency has been deleted.', 'success')

    return redirect(url_for('main.currency'))
