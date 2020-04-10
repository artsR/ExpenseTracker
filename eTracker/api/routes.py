from flask import jsonify, g, abort, request
from flask_login import current_user, login_required
from eTracker import db
from eTracker.models import Transaction, Currency, Wallet
from eTracker.api import bp
from eTracker.api.auth import token_auth
from eTracker.api.errors_handler import bad_request
from eTracker.api.models_schema import (
    CurrencySchema, WalletSchema, SubwalletSchema, CategorySchema,
    TransactionSchema, TransactionPaginationSchema
)



# Init schema:
currencies_schema = CurrencySchema(many=True)
wallets_schema = WalletSchema(many=True)
subwallets_schema = SubwalletSchema(many=True)
categories_schema = CategorySchema(many=True)
transaction_schema = TransactionSchema()
transactions_pagination_schema = TransactionPaginationSchema()


@bp.route('/transactions', methods=['GET'])
@token_auth.login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 5, type=int), 50)
    user_transactions = (
        Transaction.query
        .join(Transaction.wallet)
        .filter(Wallet.user_id==g.current_user.id)
    )
    data = user_transactions.paginate(page, per_page, False)
    transactions = transactions_pagination_schema.dump(data)
    return jsonify(transactions)


@bp.route('/transactions', methods=['POST'])
@token_auth.login_required
def new_transaction():
    json_data = request.get_json()
    errors = transaction_schema.validate(json_data)
    if errors:
        return bad_request(str(errors))

    transaction = transaction_schema.load(json_data);

    wallet = Wallet.query.get(json_data['wallet_id'])
    subwallet_id = json_data['subwallet_id']
    subwallet_is_attached_to_wallet = (
        subwallet_id in [subwallet.id for subwallet in wallet.subwallets]
    )
    if not subwallet_is_attached_to_wallet:
        return bad_request('The subwallet not attached to the wallet')

    db.session.add(transaction)
    db.session.commit()

    response = jsonify({'message': 'Transaction added correctly'})
    response.status_code = 201
    return response


@bp.route('/transactions/<transaction_id>', methods=['GET'])
@token_auth.login_required
def get_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    if (transaction is None) or (transaction.wallet.user_id != g.current_user.id):
        return bad_request('You do not have transaction with provided ID')

    data = transaction_schema.dump(transaction)
    return jsonify({'transaction': data})


@bp.route('/transactions/<transaction_id>', methods=['DELETE'])
@token_auth.login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    if (transaction is None) or (transaction.wallet.user_id != g.current_user.id):
        return bad_request('You do not have transaction with provided ID')

    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'message': 'Transaction deleted correctly'})


@bp.route('/transactions/<transaction_id>', methods=['PUT'])
@token_auth.login_required
def update_transaction(transaction_id):
    json_data = request.get_json()
    transaction = Transaction.query.filter_by(id=transaction_id).first()
    if (transaction is None) or (transaction.wallet.user_id != g.current_user.id):
        return bad_request('You do not have transaction with provided ID')

    errors = transaction_schema.validate(json_data, partial=True)
    if errors:
        return bad_request(str(errors))

    if (json_data.get('wallet_id') is not None or
        json_data.get('subwallet_id') is not None):
        # At least wallet or subwallet has been changed so validation needed:
        wallet_id = (
            json_data['wallet_id'] if 'wallet_id' in json_data
            else transaction.wallet_id
        )
        wallet = Wallet.query.get(wallet_id)
        subwallet_id = (
            json_data['subwallet_id'] if 'subwallet_id' in json_data
            else transaction.subwallet_id
        )
        subwallet_is_attached_to_wallet = (
            subwallet_id in [subwallet.id for subwallet in wallet.subwallets]
        )
        if not subwallet_is_attached_to_wallet:
            return bad_request('The subwallet not attached to the wallet')

    updated_transaction = transaction.make_updates(**json_data)
    db.session.commit()

    updated_transaction = transaction_schema.dump(updated_transaction)
    return jsonify({
        'data': updated_transaction,
        'message': 'Transaction updated correctly',
    })


@bp.route('/currency', methods=['GET'])
def currencies():
    data = Currency.query.all()
    currencies = currencies_schema.dump(data)
    return jsonify({'currency': currencies})


@bp.route('/wallets', methods=['GET'])
@token_auth.login_required
def wallets():
    data = g.current_user.wallets
    wallets = wallets_schema.dump(data)
    return jsonify({'wallet': wallets})


@bp.route('/subwallets', methods=['GET'])
@token_auth.login_required
def subwallets():
    data = g.current_user.subwallets
    subwallets = subwallets_schema.dump(data)
    return jsonify({'subwallet': subwallets})


@bp.route('/categories', methods=['GET'])
@token_auth.login_required
def categories():
    data = g.current_user.categories
    categories = categories_schema.dump(data)
    return jsonify({'category': categories})
