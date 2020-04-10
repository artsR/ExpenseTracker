from flask import g, url_for
from marshmallow import (
    Schema, fields, validate, ValidationError, validates, validates_schema, post_load
)
from eTracker.models import Transaction, Wallet



class PaginationSchema(Schema):
    page = fields.Int(dump_only=True)
    per_page = fields.Int(dump_only=True)
    pages = fields.Int(dump_only=True)
    total = fields.Int(dump_only=True)
    _links = fields.Method(serialize='get_links')

    def get_links(self, object):
        links = {
            'self': url_for('api.transactions', page=object.page,
                            per_page=object.per_page)
        }
        if object.has_prev:
            links['prev'] = url_for('api.transactions', page=object.prev_num,
                                    per_page=object.per_page)
        if object.has_next:
            links['next'] = url_for('api.transactions', page=object.next_num,
                                    per_page=object.per_page)
        links['wallet'] = url_for('api.wallets')
        links['subwallet'] = url_for('api.subwallets')
        links['category'] = url_for('api.categories')
        return links

    class Meta:
        ordered = True


class TransactionPaginationSchema(PaginationSchema):
    transactions = fields.Nested('TransactionSchema', attribute='items', many=True)


class TransactionSchema(Schema):
    id = fields.Int(dump_only=True)
    date = fields.DateTime('%Y-%m-%d', required=True)
    currency = fields.Str(dump_only=True, attribute='wallet.currency.abbr')
    wallet = fields.Nested(
        'WalletSchema', dump_only=True, only=('id', 'name',)
    )
    wallet_id = (
        fields.Int(load_only=True, required=True, validate=[validate.Range(min=1)])
    )
    subwallet = fields.Nested(
        'SubwalletSchema', dump_only=True, only=('id', 'name',)
    )
    subwallet_id = (
        fields.Int(load_only=True, required=True, validate=[validate.Range(min=1)])
    )
    amount = fields.Float(required=True)
    category = fields.Nested('CategorySchema', dump_only=True)
    category_id = (
        fields.Int(load_only=True, required=True, validate=[validate.Range(min=1)])
    )
    description = fields.Str(validate=[validate.Length(max=150)])

    class Meta:
        ordered = True

    @validates('wallet_id')
    def is_user_wallet(self, wallet_id):
        not_user_wallet = (
            wallet_id
            not in [wallet.id for wallet in g.current_user.wallets]
        )
        if not_user_wallet:
            raise ValidationError('You do not have wallet with provided ID')

    @validates('subwallet_id')
    def is_user_subwallet(self, subwallet_id):
        not_user_subwallet = (
            subwallet_id
            not in [subwallet.id for subwallet in g.current_user.subwallets]
        )
        if not_user_subwallet:
            raise ValidationError('You do not have subwallet with provided ID')

    @validates('category_id')
    def is_user_category(self, category_id):
        not_user_category = (
            category_id
            not in [category.id for category in g.current_user.categories]
        )
        if not_user_category:
            raise ValidationError('You do not have category with provided ID')

    @post_load
    def create_transaction(self, details, **kwargs):
        return Transaction(**details)


class CurrencySchema(Schema):
    id = fields.Int(dump_only=True)
    abbr = fields.Str()


class WalletSchema(Schema):
    _links = fields.Method(serialize='get_links')
    id = fields.Int(dump_only=True)
    name = fields.Str()
    currency = fields.Nested('CurrencySchema', only=('abbr',))
    subwallets = fields.Nested('SubwalletSchema', many=True, only=('id', 'name',))
    transactions = fields.Pluck('TransactionSchema', 'id', many=True)

    def get_links(self, object):
        links = {
            'self': url_for('api.wallets'),
            'currency': url_for('api.currencies')
            'subwallets': url_for('api.subwallets'),
            'transactions': url_for('api.transactions'),
        }
        return links

    class Meta:
        ordered = True


class SubwalletSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    wallets = fields.Nested('WalletSchema', many=True, exclude=('subwallets',))
    transactions = fields.Pluck('TransactionSchema', 'id', many=True)

    def get_links(self, object):
        links = {
            'self': url_for('api.subwallets'),
            'wallets': url_for('api.wallets'),
            'transactions': url_for('api.transactions'),
        }
        return links

    class Meta:
        ordered = True


class CategorySchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
