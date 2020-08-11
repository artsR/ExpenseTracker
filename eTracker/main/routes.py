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
