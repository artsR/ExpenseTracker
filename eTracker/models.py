import os
import jwt
import base64
from hashlib import  md5
from time import time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from flask_login import UserMixin
from eTracker import db, login
from sqlalchemy import and_, text



wallet_subwallet = db.Table(
    'wallet_subwallet',
    db.Column('wallet_id', db.Integer(), db.ForeignKey('wallet.id'), primary_key=True),
    db.Column('subwallet_id', db.Integer(), db.ForeignKey('subwallet.id'), primary_key=True)
)
user_currency = db.Table(
    'user_currency',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id'), primary_key=True),
    db.Column('currency_id', db.Integer(), db.ForeignKey('currency.id'), primary_key=True)
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(255), index=True, unique=True)
    email = db.Column(db.String(255), index=True, unique=True)
    pswd_hash = db.Column(db.String(255))
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    wallets = db.relationship('Wallet', lazy='dynamic',
                            cascade='all, delete-orphan',
                            backref=db.backref('user', lazy='joined'))
    subwallets = db.relationship('Subwallet', lazy='dynamic',
                            cascade='all, delete-orphan',
                            backref=db.backref('user', lazy='joined'))
    categories = db.relationship('Category', lazy='dynamic',
                            cascade='all, delete-orphan', backref='user')
    currencies = db.relationship('Currency', secondary=user_currency, lazy='dynamic')

    def transactions(self):
        return (
            db.session.query(
                Transaction.id, Transaction.date, Transaction.amount,
                Transaction.description,
                Wallet.name.label('wallet'),
                Subwallet.name.label('subwallet'),
                Currency.abbr.label('currency'),
                Category.name.label('category')
            )
            .join(Transaction.wallet)
            .join(Transaction.subwallet)
            .join(Wallet.currency)
            .join(Transaction.category)
            .filter(Wallet.user==self)
        )

    def set_password(self, password):
        self.pswd_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pswd_hash, password)

    def get_reset_password_token(self, valid=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + valid},
            current_app.config['SECRET_KEY'], algorithm='HS256'
        ).decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, current_app.config['SECRET_KEY'], algorithms=['HS256']
            )['reset_password']
        except:
            return None
        else:
            return User.query.get(id)

    def get_token(self, valid=3600):
        """Get token for API authentication/ authorization."""
        now = datetime.utcnow()
        if (self.token) and (self.token_expiration > now + timedelta(seconds=60)):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=valid)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = now - 1

    @staticmethod
    def check_token(token):
        """Get `user` by provided token for API application."""
        user = User.query.filter_by(token=token).first()
        if (user is None) or (user.token_expiration < datetime.utcnow()):
            return None
        return user

    def __repr__(self):
        return f"{self.__tablename__} <User {self.username} {self.email}>"


class Currency(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    abbr = db.Column(db.String(64), index=True)

    def __repr__(self):
        return f"{self.id}"


class Wallet(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    currency_id = db.Column(db.Integer(), db.ForeignKey('currency.id'))
    color = db.Column(db.String(7), server_default='#000000')

    currency = db.relationship('Currency')
    transactions = db.relationship('Transaction', lazy='dynamic', backref='wallet')
    subwallets = db.relationship('Subwallet',
                                secondary=wallet_subwallet,
                                lazy='dynamic',
                                backref=db.backref('wallets', lazy='dynamic'),
    )

    def balance_total(self):
        return (
            db.session.query(
            db.func.coalesce(db.func.sum(Transaction.amount), 0)
            )
            .filter_by(wallet=self).scalar()
        )

    def details(self):
        subwallets = (
            db.session.query(
                Subwallet.id, Subwallet.name,
                db.func.sum(Transaction.amount).label('total')
            )
            .join(Transaction.wallet)
            .join(Transaction.subwallet)
            .filter(Transaction.wallet==self)
            .group_by(Subwallet.id)
            .all()
        )
        return [
            {'id': subwallet.id, 'name': subwallet.name, 'total': subwallet.total}
            for subwallet in subwallets
        ]

    def __repr__(self):
        return f"{self.id}"


class Subwallet(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    name = db.Column(db.String(64))

    transactions = db.relationship('Transaction', lazy='dynamic', backref='subwallet')

    def get_balance(self, wallet_id):
        return (
            db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0))
            .join(Transaction.subwallet)
            .filter((Transaction.wallet_id==wallet_id) &
                    (Transaction.subwallet_id==self.id))
            .scalar()
        )

    def details(self):
        by_currency_wallet = (
            db.session.query(
                Currency.abbr.label('currency'),
                Wallet.name.label('wallet'),
                db.func.sum(Transaction.amount).label('total')
            )
            .join(Transaction.wallet)
            .join(Wallet.currency)
            .filter(Transaction.subwallet==self)
            .group_by(Currency.abbr, Wallet.id)
            .order_by(Currency.abbr)
            .all()
        )
        return [{
            'currency': by.currency,
            'wallet': by.wallet,
            'total': by.total
            } for by in by_currency_wallet
        ]

    def __repr__(self):
        return f"{self.id}"


class Transaction(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    wallet_id = db.Column(db.Integer(), db.ForeignKey('wallet.id'))
    subwallet_id = db.Column(db.Integer(), db.ForeignKey('subwallet.id'))
    amount = db.Column(db.Float(precision='2'))
    category_id = db.Column(db.Integer(), db.ForeignKey('category.id'))
    description = db.Column(db.String(256))

    @staticmethod
    def apply_filters(query, filters):
        """Apply filters for `current_user` `transactions`."""
        if filters.get('date_start'):
            query = query.filter(
                db.cast(Transaction.date, db.Date) >= filters.get('date_start')
            )
        if filters.get('date_end'):
            query = query.filter(
                db.cast(Transaction.date, db.Date) <= filters.get('date_end')
            )
        if filters.get('amount_min'):
            query = query.filter(
                Transaction.amount >= filters.get('amount_min')
            )
        if filters.get('amount_max'):
            query = query.filter(
                Transaction.amount <= filters.get('amount_max')
            )
        if filters.get('currencies'):
            query = query.filter(Currency.id.in_(
                item.id for item in filters.get('currencies'))
            )
        if filters.get('wallets'):
            query = query.filter(Wallet.id.in_(
                item.id for item in filters.get('wallets'))
            )
        if filters.get('subwallets'):
            query = query.filter(Subwallet.id.in_(
                item.id for item in filters.get('subwallets'))
            )
        if filters.get('categories'):
            query = query.filter(Category.id.in_(
                item.id for item in filters.get('categories'))
            )
        return query

    def make_updates(self, **fields):
        for k, v in fields.items():
            setattr(self, k, v)
        return self

    def __repr__(self):
        return (
            f"<Transaction: {self.date}, {self.subwallet_id}, "
            f"{self.wallet.currency}, {self.amount}\n"
            f"Description: {self.description}>"
        )


class Category(db.Model):
    __table_args__ = (
        db.UniqueConstraint('user_id', 'name', name='_user_id_name'),
    )

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    name = db.Column(db.String(64))

    transactions = db.relationship('Transaction', lazy='dynamic', backref='category')

    def __repr__(self):
        return f"<Category {self.name}>"



@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
