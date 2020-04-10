import os
import requests
from datetime import datetime, date
from flask import render_template, redirect, url_for, flash, abort, jsonify, request
from flask import current_app
from flask_login import current_user, login_required
from eTracker import db
from eTracker.models import (
    User, Currency, Wallet, Subwallet, Transaction, Category
)
from eTracker.main import bp
from eTracker.main.forms import (
    UploadForm, WalletForm, WalletsSubwallets, FiltersForm, TransactionForm
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


@bp.route('/tools/c/', methods=['GET', 'POST'])
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


@bp.route('/tools/c/delete/', methods=['POST'])
@login_required
def delete_c():

    if int(request.form['id']) == current_user.currency_default_choice:
        flash('You cannot delete your default currency', 'danger')
        return redirect(url_for('main.currency'))

    currency = Currency.query.get_or_404(request.form['id'])
    if currency.user != current_user:
        abort(403)
    flash(request.form)
    flash('Currency has been deleted.', 'success')

    return redirect(url_for('main.currency'))


@bp.route('/tools/c/default/', methods=['POST'])
@login_required
def default_c():

    curr_id = request.form['curr_id']

    user = User.query.filter_by(username=current_user.username).first()
    user.currency_default = Currency.query.filter_by(id=curr_id).first()
    db.session.commit()
    flash('Your default currency has been updated.', 'success')

    return url_for('main.currency')


@bp.route('/wallets/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@bp.route('/wallets/dashboard_group')
@login_required
def dashboard_group():

    groups = request.args.getlist('groups')
    transactions = current_user.transactions().subquery()
    groups_list = [
        getattr(transactions.c, group) for group in groups
    ]
    result = (
        db.session.query(
            *groups_list,
            db.func.sum(transactions.c.amount),
            transactions.c.currency
        )
        .group_by(*groups_list, transactions.c.currency)
        .all()
    )

    return jsonify({'balance': result})


@bp.route('/wallets/', methods=['GET'])
@login_required
def wallets():

    form = WalletForm()
    currency_options = db.session.query(Currency.id, Currency.abbr)
    form.currency.choices = [
        (currency.id, currency.abbr)
        for currency in currency_options
    ]

    wallets = current_user.wallets
    categories = current_user.categories

    return render_template('wallets.html', form=form, wallets=wallets,
                        categories=categories)


@bp.route('/wallets/<int:wallet_id>', methods=['GET'])
@login_required
def wallet_details(wallet_id):
    """Send details for Wallet with particular ID."""
    wallet = (
        Wallet.query
        .filter((Wallet.user_id==current_user.id) &
                (Wallet.id==wallet_id))
        .first_or_404()
    )
    subwallets = [
        {'id': subwallet.id, 'name': subwallet.name}
        for subwallet in wallet.subwallets
    ]
    currency = wallet.currency

    return jsonify({
        'name': wallet.name,
        'color': wallet.color,
        'currency': {'abbr': currency.abbr, 'id': currency.id},
        'subwallets': subwallets,
    })


@bp.route('/wallets/subwallet/add', methods=['GET', 'POST'])
@login_required
def add_subwallet():
    """Adds subwallet to the wallet."""
    form = WalletsSubwallets()

    if form.validate_on_submit():
        wallet = form.subwallet_wallets.data
        subwallet = form.subwallet_subwallets.data

        if wallet.user != current_user:
            abort(403)
        if subwallet.user != current_user:
            abort(403)

        if subwallet not in wallet.subwallets:
            wallet.subwallets.append(subwallet)
            db.session.add(wallet)
            db.session.commit()
            flash('Subwallet added successfully', 'success')
            return redirect(url_for('main.wallets'))
        else:
            flash('Wallet has already had subwallet with this name', 'warning')
            return redirect(url_for('main.tools'))

    return render_template('add_subwallet.html', form=form)


@bp.route('/wallets/subwallet/remove', methods=['POST'])
@login_required
def remove_subwallet():
    """Removes subwallet from the wallet."""
    if request.method == 'POST':
        wallet = Wallet.query.get_or_404(request.form['wallet_id'])
        subwallet = Subwallet.query.get_or_404(request.form['subwallet_id'])

        if wallet.user != current_user:
            abort(403)
        if subwallet.user != current_user:
            abort(403)

        if wallet.transactions.all() and subwallet.transactions.all():
            flash('You cannot remove subwallet with transaction', 'danger')
            return redirect(url_for('main.transactions'))

        wallet.subwallets.remove(subwallet)
        db.session.commit()
        flash('Subwallet has been removed successfully', 'success')
        return redirect(url_for('main.tools'))


@bp.route('/tools/')
@login_required
def tools():
    currencies = Currency.query
    return render_template('tools.html', currencies=currencies)


@bp.route('/tools/wallet/new', methods=['POST'])
@login_required
def new_wallet():

    if request.method == 'POST':
        wallet = current_user.wallets.filter(
            Wallet.name==request.form['wallet_name']).first()
        if wallet is not None:
            flash('You already has wallet with that name', 'danger')
            return redirect(url_for('main.wallets'))
        wallet = Wallet(
            name=request.form['wallet_name'].strip(),
            user_id=current_user.id,
            currency_id=request.form['currency'],
            color=request.form['wallet_color'],
        )
        db.session.add(wallet)
        db.session.commit()
        flash('New wallet added successfully.', 'success')

    else:
        flash('Something went wrong. Please try again', 'danger')

    return redirect(url_for('main.wallets'))


@bp.route('/tools/wallet/update/', methods=['POST'])
@login_required
def update_wallet():

    if request.method == 'POST':
        wallet = Wallet.query.get_or_404(request.form['wallet_id'])
        if wallet.user != current_user:
            abort(403)

        if wallet.name != request.form['wallet_name']:
            not_unique = (
                current_user.wallets
                .filter_by(name=request.form['wallet_name'])
                .first() is not None
            )
            if not_unique:
                flash('This wallet name is already in use', 'danger')
            else:
                wallet.name = request.form['wallet_name']
                wallet.color = request.form['wallet_color']
                db.session.commit()
                flash('Change made successfully', 'success')
        else:
            wallet.color = request.form['wallet_color']
            db.session.commit()
            flash('Change made successfully', 'success')

    return redirect(url_for('main.wallets'))


@bp.route('/tools/wallet/delete/', methods=['POST'])
@login_required
def delete_wallet():

    wallet = Wallet.query.get_or_404(request.form['wallet_id'])
    if wallet.user != current_user:
        abort(403)

    if wallet.transactions.all():
        flash('You cannot delete wallet associated to the transaction', 'danger')
        return redirect(url_for('main.transactions'))

    db.session.delete(wallet)
    db.session.commit()
    flash('Wallet has been deleted.', 'success')
    return redirect(url_for('main.wallets'))


@bp.route('/tools/subwallet/new', methods=['POST'])
@login_required
def new_subwallet():

    subwallet = current_user.subwallets.filter_by(name=request.form['name']).first()
    if subwallet is not None:
        flash('You already have subwallet with that name', 'danger')
        return redirect(url_for('main.tools'))

    current_user.subwallets.append(Subwallet(name=request.form['name']))
    db.session.commit()
    flash('Subwallet has been added successfully', 'success')
    return redirect(url_for('main.tools'))


@bp.route('/tools/subwallet/update', methods=['POST'])
@login_required
def update_subwallet():

    if request.method == 'POST':
        subwallet = Subwallet.query.get_or_404(request.form['subwallet_id'])
        if subwallet.user != current_user:
            abort(403)

        if subwallet.name != request.form['subwallet_name']:
            not_unique = (
                current_user.subwallets
                .filter_by(name=request.form['subwallet_name'])
                .first() is not None
            )
            if not_unique:
                flash('This subwallet name is already in use', 'danger')
            else:
                subwallet.name = request.form['subwallet_name']
                db.session.commit()
                flash('Change made successfully', 'success')

    return redirect(url_for('main.tools'))


@bp.route('/tools/subwallet/delete', methods=['POST'])
@login_required
def delete_subwallet():

    subwallet = Subwallet.query.get_or_404(request.form['subwallet_id'])
    if subwallet.user != current_user:
        abort(403)

    if subwallet.transactions.all():
        flash('You cannot delete subwallet associated to the transaction', 'danger')
        return redirect(url_for('main.transactions'))

    db.session.delete(subwallet)
    db.session.commit()
    flash('Subwallet has been deleted', 'success')
    return redirect(url_for('main.tools'))


@bp.route('/tools/category/new', methods=['POST'])
@login_required
def new_category():

    category = current_user.categories.filter_by(name=request.form['name']).first()
    if category is not None:
        flash('You already have category with that name', 'danger')
        return redirect(url_for('main.tools'))

    current_user.categories.append(Category(name=request.form['name']))
    db.session.commit()
    flash('Category has been added successfully', 'success')
    return redirect(url_for('main.tools'))


@bp.route('/tools/category/update', methods=['POST'])
@login_required
def update_category():

    if request.method == 'POST':
        category = Category.query.get_or_404(request.form['category_id'])
        if category.user != current_user:
            abort(403)

        if category.name != request.form['category_name']:
            not_unique = (
                current_user.categories
                .filter_by(name=request.form['category_name'])
                .first() is not None
            )
            if not_unique:
                flash('This category name is already in use', 'danger')
            else:
                category.name = request.form['category_name']
                db.session.commit()
                flash('Change made successfully', 'success')

    return redirect(url_for('main.tools'))


@bp.route('/tools/category/delete', methods=['POST'])
@login_required
def delete_category():

    category = Category.query.get_or_404(request.form['category_id'])
    if category.user != current_user:
        abort(403)

    if category.transactions.all():
        flash('You cannot delete category associated to the transaction', 'danger')
        return redirect(url_for('main.transactions'))

    db.session.delete(category)
    db.session.commit()
    flash('Category has been deleted', 'success')
    return redirect(url_for('main.tools'))


@bp.route('/tools/currency/add', methods=['POST'])
@login_required
def add_currency():

    currency = Currency.query.get_or_404(request.form['currency_id'])
    if currency in current_user.currencies:
        flash('You cannot add the same currency twice', 'danger')
        return redirect(url_for('main.tools'))

    current_user.currencies.append(currency)
    db.session.commit()
    flash('Currency has been added successfully', 'success')
    return redirect(url_for('main.tools'))


@bp.route('/tools/currency/remove', methods=['POST'])
@login_required
def remove_currency():

    currency = current_user.currencies.filter_by(
        id=request.form['currency_id']
        ).first_or_404()
    current_user.currencies.remove(currency)
    db.session.commit()
    flash('Currency has been removed successfully', 'success')
    return redirect(url_for('main.tools'))


@bp.route('/tools/xrate/', methods=['GET'])
def exchange_rate():
    return render_template('tools_xrate.html')


@bp.route('/tools/xrate_popup/<base>/<amount>')
@login_required
def xrate_popup(base, amount):

    r = requests.get(f'https://api.exchangeratesapi.io/latest?'
                        f'base={base}')
    xrates = r.json()['rates'] if r.status_code == 200 else r.json()['error']

    return render_template('xrate_popup.html', xrates=xrates,
                        amount=float(amount), base=base)


@bp.route('/cashflow/new/transfer/', methods=['POST'])
@login_required
def transfer():

    if request.method == 'POST':
        subwallet = Subwallet.query.filter(
            Subwallet.id==request.form['subwallet_id1']
            ).first()
        wallet = Wallet.query.get_or_404(request.form['wallet_id1'])
        if (wallet.user != current_user) or (subwallet not in wallet.subwallets):
            abort(403)

        has_enough_funds = (
            subwallet.get_balance(wallet.id)
            >= float(request.form['sent_amount'])
        )
        if has_enough_funds:
            transaction_from = Transaction(
                wallet_id=request.form['wallet_id1'],
                subwallet_id=request.form['subwallet_id1'],
                category_id=request.form['category_id'],
                amount=-abs(float(request.form['sent_amount'])),
                description=request.form['description'],
            )
            transaction_to = Transaction(
                wallet_id=request.form['wallet_id2'],
                subwallet_id=request.form['subwallet_id2'],
                category_id=request.form['category_id'],
                amount=abs(float(request.form['received_amount'])),
                description=request.form['description'],
            )
            db.session.add_all([transaction_from, transaction_to])
            db.session.commit()
            flash(request.form)
            flash('Transfer was recorded successfully.','success')
        else:
            flash('You don\'t have enough funds.','danger')

        return redirect(url_for('main.wallets'))


@bp.route('/cashflow/new/income/', methods=['POST'])
@login_required
def income():

    if request.method == 'POST':
        wallet = Wallet.query.get_or_404(request.form['wallet_id'])
        if wallet.user != current_user:
            abort(403)

        subwallet = Subwallet.query.get_or_404(request.form['subwallet_id'])
        if subwallet not in wallet.subwallets:
            abort(403)

        transaction_income = Transaction(
            date=request.form['transaction_date'],
            wallet_id=request.form['wallet_id'],
            subwallet_id=request.form['subwallet_id'],
            category_id=request.form['category_id'],
            amount=abs(float(request.form['amount'])),
            description=request.form['description'],
        )
        db.session.add(transaction_income)
        db.session.commit()
        flash('Deposit added successfully.', 'success')

        return redirect(url_for('main.wallets'))


@bp.route('/cashflow/new/expense/', methods=['POST'])
@login_required
def expense():

    if request.method == 'POST':
        wallet = Wallet.query.get_or_404(request.form['wallet_id'])
        if wallet.user != current_user:
            abort(403)

        subwallet = Subwallet.query.get_or_404(request.form['subwallet_id'])
        if subwallet not in wallet.subwallets:
            abort(403)

        has_enough_funds = (
            subwallet.get_balance(request.form['wallet_id'])
            >= float(request.form['amount'])
        )
        if has_enough_funds:
            transaction_income = Transaction(
                date=request.form['transaction_date'],
                wallet_id=request.form['wallet_id'],
                subwallet_id=request.form['subwallet_id'],
                category_id=request.form['category_id'],
                amount=-abs(float(request.form['amount'])),
                description=request.form['description'],
            )
            db.session.add(transaction_income)
            db.session.commit()
            flash('Withdraw made successfully.', 'success')
        else:
            flash('You don\'t have enough funds.', 'danger')

        return redirect(url_for('main.wallets'))


@bp.route('/cashflow')
@login_required
def cashflow():
    return redirect(url_for('main.transactions'))


@bp.route('/cashflow/transactions/', methods=['GET'])
@login_required
def transactions():

    form = FiltersForm(request.args, meta={'csrf': False})
    filters = form.data

    q_transactions = current_user.transactions()
    q_transactions = Transaction.apply_filters(q_transactions, filters)

    per_page = (
        request.args.get('per_page', 0, type=int)
        if request.args.get('per_page', 0, type=int)
        else current_app.config['EXP_PER_PAGE']
    )
    page = request.args.get('page', 1, type=int)

    q_transactions = q_transactions.paginate(page, per_page, 0)
    q_url = {k: v for k, v in filters.items() if k not in ['submit']}
    next_url = (
        url_for('main.transactions', page=q_transactions.next_num, per_page=per_page,
                **q_url)
        if q_transactions.has_next else None
    )
    prev_url = (
        url_for('main.transactions', page=q_transactions.prev_num, per_page=per_page,
                **q_url)
        if q_transactions.has_prev else None
    )

    return render_template('transactions.html', transactions=q_transactions,
                        next_url=next_url, prev_url=prev_url, form=form,
                        filters=q_url)


@bp.route('/cashflow/delete', methods=['POST'])
@login_required
def delete_transaction():
    transaction = Transaction.query.get_or_404(request.form['transaction_id'])
    if transaction.wallet.user != current_user:
        abort(403)

    # transaction.delete()
    # db.session.commit()
    flash('Transaction was deleted', 'success')
    return redirect(url_for('main.transactions'))


@bp.route('/cashflow/<transaction_id>/update', methods=['GET', 'POST'])
@login_required
def update_transaction(transaction_id):

    transaction = Transaction.query.get_or_404(transaction_id)
    if transaction.wallet.user != current_user:
        abort(403)
    form = TransactionForm(obj=transaction)
    form.subwallet.choices = [
        (subwallet.id, subwallet.name)
        for subwallet in transaction.wallet.subwallets
    ]
    if form.validate_on_submit():
        transaction = Transaction.query.get_or_404(form.transaction_id.data)
        if transaction.wallet.user != current_user:
            abort(403)

        transaction.date = form.date.data
        transaction.wallet_id = form.wallet.data.id
        transaction.subwallet_id = form.subwallet.data
        transaction.amount = form.amount.data
        transaction.category_id = form.category.data.id
        transaction.description = form.description.data
        db.session.add(transaction)
        db.session.commit()
        flash('Changes made successfully', 'success')
        return redirect(url_for('main.transactions'))

    form.transaction_id.data = transaction_id
    form.subwallet.default = transaction.subwallet_id
    currency = transaction.wallet.currency.abbr

    return render_template('transactions_update.html', form=form,
                            currency=currency, t_id=transaction_id)


@bp.route('/planning')
@login_required
def planning():
    return render_template('planning.html')


@bp.route('/testing', methods=['GET', 'POST'])
def testing():
    import sys
    from flask import session
    from sqlalchemy.ext.serializer import loads, dumps

    form = FiltersForm(request.args)

    if session.get('t') is not None:
        print('|'*80)
        print(loads(session.get('t')), file=sys.stdout)
        print('|'*80)
    if session.get('txt') is not None:
        print('.'*80)
        print(session.get('txt'))
    print('*'*80)
    print(request.args.get('page'), file=sys.stdout)
    print('*'*80)
    print('-'*80)
    print('url:')
    print(request.url, file=sys.stdout)
    print('-'*80)
    print('path:')
    print(request.path, file=sys.stdout)
    print('@'*80)
    print('full_path:')
    print(request.full_path, file=sys.stdout)
    print('#'*80)
    print('query_string:')
    print(request.query_string, file=sys.stdout)
    print('='*80)
    # form.currencies.choices.insert(0, ('', ''))

    filters = form.data
    q_transactions = current_user.transactions()
    q_transactions = Transaction.apply_filters(q_transactions, filters)
    session['txt'] = 'some nice text'
    # session['t'] = dumps(q_transactions)
    #return redirect(url_for('main.testing'))

    return render_template('test_edit_transaction.html', form=form)

@bp.route('/test_popup')
def test_popup():
    return render_template('xrate_popup.html')

@bp.route('/test_cashflow_update')
def test_update_cashflow():
    transaction = Transaction.query.get_or_404(3)
    form = TransactionForm(request.form, obj=transaction)

    form.subwallet.choices = [
        (subwallet.id, subwallet.name)
        for subwallet in transaction.wallet.subwallets
    ]
    form.subwallet.default = transaction.subwallet_id
    form.currency.data = transaction.wallet.currency.abbr

    return render_template('cashflow_update.html', form=form)
