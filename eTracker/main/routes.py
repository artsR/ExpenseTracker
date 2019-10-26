import os
from flask import render_template, redirect, url_for, flash, abort
from flask import current_app
from flask_login import current_user, login_required
from eTracker import db
from eTracker.models import User, Expense, Currency
from eTracker.main import bp
from eTracker.main.forms import AddExpenseForm, UploadForm, CurrencyForm
from werkzeug.utils import secure_filename
import flask



@bp.route('/index')
@bp.route('/')
def index():

    return render_template('index.html')


@bp.route('/test')
def test():
    return render_template('test.html')


@bp.route('/expenses')
@login_required
def expenses():
    return render_template('expenses.html')


@bp.route('/spendings')
@login_required
def spendings():

    #form = someForm_to_modified_raw

    per_page = current_app.config['EXP_PER_PAGE']
    page = flask.request.args.get('page', 1, type=int)
    expenses = current_user.spendings().paginate(
                    page, per_page, 0)
    next_url = ( url_for('main.spendings', page=expenses.next_num)
        if expenses.has_next else None )
    prev_url = ( url_for('main.spendings', page=expenses.prev_num)
        if expenses.has_prev else None )

    if flask.request.method == 'POST':
        #modify raw in database
        pass

    return render_template('spendings.html', expenses=expenses,
                        next_url=next_url, prev_url=prev_url)


@bp.route('/expenses/edit_spending/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):

    expense = Expense.query.get_or_404(expense_id)

    if expense.user != current_user:
        abort(403)

    form = AddExpenseForm()

    if form.validate_on_submit():

        redirect(url_for('main.spendings'))
        pass

    form.expenseDate.data = expense.expenseDate
    form.product.data = expense.product
    form.category.data = expense.category
    form.freq.data = expense.freq
    form.quantity.data = expense.quantity
    form.price.data = expense.price
    form.currency.data = expense.currency

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



@bp.route('/expenses_add', methods=['GET', 'POST'])
@login_required
def expenses_add():

    form = AddExpenseForm()

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


@bp.route('/tools')
def tools():
    return render_template('tools.html')


@bp.route('/tools/category')
@login_required
def category():

    q = current_user.get_groups(category).all()
    categories = [(i, exp.category) for i, exp in enumerate(q, 1)]

    return render_template('tools_category.html', categories=categories)


@bp.route('/tools/currency', methods=['GET', 'POST'])
def currency():

    form = CurrencyForm()

    if form.validate_on_submit():
        currency = Currency(abv=form.abv.data.upper(), name=form.name.data,
                        user=current_user)
        db.session.add(currency)
        db.session.commit()
        flash('Currency was added into your account.', 'success')
        redirect(url_for('main.currency'))

    currs = Currency.query.filter_by(user = current_user).group_by(Currency.name)

    return render_template('tools_currency.html', currs=currs, form=form)
