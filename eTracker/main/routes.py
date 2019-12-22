import os
from datetime import date
from flask import render_template, redirect, url_for, flash, abort, jsonify, request
from flask import current_app
from flask_login import current_user, login_required
from eTracker import db
from eTracker.models import (
    User, Expense, Currency, CurrencyOfficialAbbr, Wallet, Subwallet,
    Transaction
)
from eTracker.main import bp
from eTracker.main.forms import (
    AddExpenseForm, UploadForm, CurrencyForm, FiltersForm, WalletForm
)
from werkzeug.utils import secure_filename



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
    return render_template('cashflow.html')


@bp.route('/transactions/', methods=['GET'])
@login_required
def transactions():

    per_page = (
        request.args.get('per_page', 0, type=int)
        if request.args.get('per_page', 0, type=int)
        else current_app.config['EXP_PER_PAGE']
    )
    page = request.args.get('page', 1, type=int)

    transactions = current_user.transactions.paginate(
        page, per_page, 0)

    next_url = (
        url_for('main.transactions', page=transactions.next_num, per_page=per_page)
        if transactions.has_next else None
    )
    prev_url = (
        url_for('main.transactions', page=transactions.prev_num, per_page=per_page)
        if transactions.has_prev else None
    )

    form = FiltersForm()

    return render_template('transactions.html', transactions=transactions,
                        next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/spendings', methods=['GET', 'POST'])
@login_required
def spendings():

    per_page = (
        request.args.get('per_page', 0, type=int)
        if request.args.get('per_page', 0, type=int)
        else current_app.config['EXP_PER_PAGE']
    )
    page = request.args.get('page', 1, type=int)

    form = FiltersForm()
    # form.category.choices = [
    #     (col.category.lower(), col.category)
    #     for col in current_user.get_categories().all()
    # ]
    # form.freq.choices = [
    #     (col.freq.lower(), col.freq)
    #     for col in db.session.query(Expense.freq).filter(
    #         Expense.user == current_user).group_by(
    #         Expense.freq).all()
    # ]

    expenses = current_user.get_spendings().paginate(
        page, per_page, 0)
    next_url = (
        url_for('main.spendings', page=expenses.next_num, per_page=per_page)
        if expenses.has_next else None
    )
    prev_url = (
        url_for('main.spendings', page=expenses.prev_num, per_page=per_page)
        if expenses.has_prev else None
    )

    return render_template('spendings.html', form=form, expenses=expenses,
                        next_url=next_url, prev_url=prev_url)


@bp.route('/expenses/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):

    expense = Expense.query.get_or_404(expense_id)

    if expense.user != current_user:
        abort(403)

    form = AddExpenseForm()
    currency_grp = db.session.query(Currency.abbr).filter_by(user=current_user).all()
    form.currency.choices = [(curr[0], curr[0]) for curr in currency_grp]

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

    # elif request.method == 'GET':
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
    form.expenseDate.data = date.today()

    currency_official = CurrencyOfficialAbbr.getCurrency().all()
    form.currency.choices = [(curr.id, curr.abbr) for curr in currency_official]

    wallet_choices = Wallet.query.filter_by(user=current_user).all()
    wallets = [(wallet.id, wallet.name) for wallet in wallet_choices]

    if request.method == 'POST':
        transaction = Transaction(
            user_id=current_user.id,
            wallet_id=form.wallet_id.data,
            subwallet_id=form.subwallet_id.data,
            type='Expense',
            currency_id=form.currency.data,
            amount=-abs(form.price.data), #or sum of prices in receipt
        )
        db.session.add(transaction)
        db.session.commit()
        # for expense in expenses (one receipt can contain many expenses)
        # expense = Expense(
        #     expenseDate=form.expenseDate.data, product=form.product.data,
        #     category=form.category.data, freq=form.freq.data,
        #     quantity=form.quantity.data, price=form.price.data,
        #     currency=form.currency.data, user=current_user,
        #     transaction_id=transaction.id,
        # )
        # transaction.expenses.append(expense)
        # db.session.commit()
        flash('Expense added to you account.', 'success')
        return redirect(url_for('main.expenses_add'))

    return render_template('add_expense.html', form=form, wallets=wallets)


@bp.route('/upload')
@login_required
def upload():

    form = UploadForm()

    if request.method == 'POST':
        if 'customFile' not in request.files:
            flash("File wasn't uploaded correctly. Please try again", "danger")
            return redirect(url_for('main.upload'))

        f = request.files['customFile']
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

    if request.method == 'POST':
        if 'customFile' not in request.files:
            flash("File wasn't uploaded correctly. Please try again", "danger")
            return redirect(url_for('main.upload'))

        f = request.files['customFile']
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
    official_currencies = db.session.query(CurrencyOfficialAbbr.abbr).all()
    form.abbr.choices = [(curr.abbr, curr.abbr) for curr in official_currencies]

    if form.validate_on_submit():
        currency = Currency(
            abbr=form.abbr.data.upper(),
            name=form.name.data,
            user=current_user,
        )
        db.session.add(currency)
        db.session.commit()
        flash('Currency was added into your account.', 'success')
        return redirect(url_for('main.currency'))

    currs = current_user.currency

    return render_template('tools_currency.html', currs=currs, form=form)


@bp.route('/tools/currency/delete/', methods=['POST'])
@login_required
def delete_currency():

    if int(request.form['id']) == current_user.currency_default_choice:
        flash('You cannot delete your default currency', 'danger')
        return redirect(url_for('main.currency'))

    currency = Currency.query.get_or_404(request.form['id'])
    if currency.user != current_user:
        abort(403)
    flash(request.form)
    flash('Currency has been deleted.', 'success')

    return redirect(url_for('main.currency'))


@bp.route('/tools/currency/default/', methods=['POST'])
@login_required
def default_currency():

    curr_id = request.form['curr_id']

    user = User.query.filter_by(username=current_user.username).first()
    user.currency_default = Currency.query.filter_by(id=curr_id).first()
    db.session.commit()
    flash('Your default currency has been updated.', 'success')

    return url_for('main.currency')


@bp.route('/wallet/dashboard')
@login_required
def wallet_dashboard():
    return render_template('wallets.html')


@bp.route('/wallets/', methods=['GET', 'POST'])
@login_required
def wallets():

    form = WalletForm()
    currency_official = CurrencyOfficialAbbr.getCurrency().all()
    form.currency.choices = [(curr.id, curr.abbr) for curr in currency_official]

    if form.validate_on_submit():
        wallet = Wallet(
            name=form.name.data,
            user_id=current_user.id,
            currency=form.currency.data,
            color=form.color.data,
        )
        db.session.add(wallet)
        db.session.commit()
        subwallet = Subwallet(
            user_id=current_user.id,
            wallet_id=wallet.id,
            name='General',
        )
        wallet.subwallets.append(subwallet)
        db.session.commit()
        # Add Transaction row to initialize wallet Balance
        # Add Transfer row to initialize subwallet Balance
        flash('New wallet added successfully.', 'success')
        flash(form.data)
        return redirect(url_for('main.wallets'))

    wallets = current_user.wallets

    return render_template('wallets.html', form=form, wallets=wallets)


@bp.route('/wallet/delete/', methods=['POST'])
@login_required
def delete_wallet():

    wallet = Wallet.query.get_or_404(request.form['id'])
    if wallet.user_id != current_user.id:
        abort(403)

    flash(request.form)
    flash('Wallet has been deleted.', 'success')

    return redirect(url_for('main.wallets'))


@bp.route('/wallet/subwallets/', methods=['GET', 'POST'])
@login_required
def add_subwallet():
    # if get sent currency of wallet
    # if post wallet.add_subwallet(name='General')
    if request.method == 'POST':
        wallet = Wallet.query.filter_by(id=request.form['wallet_id']).first()
        subwallet = Subwallet.query.filter(
            (Subwallet.wallet == wallet) &
            (Subwallet.name == request.form['name'])
        ).first()
        if not subwallet:
            subwallet = Subwallet(
                user_id=current_user.id,
                wallet_id=request.form['wallet_id'],
                name=request.form['name'],
            )
            wallet.subwallets.append(subwallet)
            db.session.commit()
            flash(request.form)
            return redirect(url_for('main.wallets'))
        else:
            flash('You cannot use the same name within one wallet', 'danger')
            return redirect(url_for('main.wallets'))


@bp.route('/income/', methods=['POST'])
@login_required
def income():

    if request.method == 'POST':
        transaction_income = Transaction(
            user_id=current_user.id,
            wallet_id=request.form['wallet_id'],
            subwallet_id=request.form['subwallet_id'],
            currency_id=request.form['currency_id'],
            type='Income',
            amount=abs(float(request.form['amount'])),
        )
        db.session.add(transaction_income)
        db.session.commit()
        flash('Deposit added successfully.', 'success')
        return redirect(url_for('main.wallets'))


@bp.route('/expense/', methods=['POST'])
@login_required
def expense():

    if request.method == 'POST':
        transaction_income = Transaction(
            user_id=current_user.id,
            wallet_id=request.form['wallet_id'],
            subwallet_id=request.form['subwallet_id'],
            currency_id=request.form['currency_id'],
            type='Expense',
            amount=-abs(float(request.form['amount'])),
        )
        db.session.add(transaction_income)
        db.session.commit()
        flash('Withdraw made successfully.', 'success')
        return redirect(url_for('main.wallets'))


@bp.route('/transfer/', methods=['POST'])
@login_required
def transfer():

    if request.method == 'POST':
        transaction_from = Transaction(
            user_id=current_user.id,
            wallet_id=request.form['wallet_id1'],
            subwallet_id=request.form['subwallet_id1'],
            currency_id=request.form['currency_id1'],
            type='Internal',
            amount=-abs(float(request.form['sent_amount'])),
        )
        transaction_to = Transaction(
            user_id=current_user.id,
            wallet_id=request.form['wallet_id2'],
            subwallet_id=request.form['subwallet_id2'],
            currency_id=request.form['currency_id2'],
            type='Internal',
            amount=abs(float(request.form['received_amount'])),
        )
        db.session.add_all([transaction_from, transaction_to])
        db.session.commit()
        flash(request.form)
        flash('Transfer was recorded successfully.','success')
        return redirect(url_for('main.wallets'))


@bp.route('/transfer/<int:wallet_id>', methods=['GET'])
@login_required
def subwallet(wallet_id):

    wallet = Wallet.query.filter(
        (Wallet.user_id == current_user.id) &
        (Wallet.id == wallet_id)
    ).first()

    subwallets = [
        {'id': subwallet.id, 'name': subwallet.name}
        for subwallet in wallet.subwallets
    ]
    currency = db.session.query(CurrencyOfficialAbbr).join(Wallet,
        CurrencyOfficialAbbr.id == wallet.currency
    ).first()

    return jsonify({
        'subwallets': subwallets,
        'currency': {'abbr': currency.abbr, 'id': currency.id}
    })
