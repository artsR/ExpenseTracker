from hashlib import  md5
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from eTracker import db, login
from sqlalchemy import and_, text



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(64), index=True, unique=True)
    pswd_hash = db.Column(db.String(128))
    currency_default_choice = db.Column(db.Integer, db.ForeignKey('currency.id'))
    expenses = db.relationship('Expense', backref='user')
    currency = db.relationship(
            'Currency',
            backref='user',
            foreign_keys="Currency.user_id"
    )
    currency_default = db.relationship(
          'Currency',
          foreign_keys='User.currency_default_choice',
          uselist=False,
    )
    wallets = db.relationship('Wallet', backref='user')
    subwallets = db.relationship('Subwallet')
    transactions = db.relationship('Transaction', lazy='dynamic')

    def add_password(self, password):
        self.pswd_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pswd_hash, password)

    def get_categories(self):
        return db.session.query(Expense.category).filter(
            Expense.user == self).group_by(Expense.category)

    def get_spendings(self, filters=''):
        return db.session.query(Expense.id,
                                Expense.expenseDate, Expense.product,
                                Expense.category, Expense.freq,
                                Expense.quantity, Expense.price,
                                Expense.currency).filter(
                                Expense.user == self)
    def get_transactions(self):
        return

    def __repr__(self):
        return f"<User(id= {self.id}, username = {self.username}, email = {self.email})>"


class Expense(db.Model):
    id = db.Column(db.Integer, db.Sequence('expense_id_seq'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))
    expenseDate = db.Column(db.Date, index=True)
    product = db.Column(db.String(140), index=True)
    category = db.Column(db.String(140), index=True)
    freq = db.Column(db.String(64))#list
    quantity = db.Column(db.Float())
    price = db.Column(db.Float(precision='2'))
    currency = db.Column(db.String(10))#list

    def __repr__(self):
        return f"<Expense {self.id} {self.product} {self.category} {self.price}>"


# class Income(db.Model):
#     id = db.Column(db.Integer, db.Sequence('income_id_seq'), primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))
#     incomeDate = db.Column(db.Date, index=True)
#     category = db.Column(db.String(140), index=True)
#     amount = db.Column(db.Float(precision='2'))


class CurrencyOfficialAbbr(db.Model):
    __tablename__ = "currency_official_abbr"
    id = db.Column(db.Integer, primary_key=True)
    abbr = db.Column(db.String(10), unique=True)
    name = db.Column(db.String(64))
    #currencies_user = db.relationship('Currency')

    @staticmethod
    def getCurrency():
        return db.session.query(CurrencyOfficialAbbr.id, CurrencyOfficialAbbr.abbr)

    def __repr__(self):
        return f"<Currency {self.id} {self.abbr} {self.name}>"


class Currency(db.Model):
    id = db.Column(db.Integer, db.Sequence('expense_id_seq'), primary_key=True)
    abbr = db.Column(db.String(10), db.ForeignKey('currency_official_abbr.abbr'))
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # transactions = db.relationship('Transaction')
    # currency_default = db.relationship(
    #         'User',
    #         foreign_keys='User.currency_default_choice',
    #         backref='currency_default',
    #         uselist=False,
    #         post_update=True,
    # )

    #subwallets = db.relationship('Transaction', back_populates='currency')

    def __repr__(self):
        return f"<Currency {self.id} {self.abbr} {self.name}>"


class Wallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    currency = db.Column(db.Integer, db.ForeignKey('currency.id'))
    color = db.Column(db.String(7))

    user_currency = db.relationship('Currency', backref='wallets')
    subwallets = db.relationship('Subwallet', backref='wallet')
    transactions = db.relationship('Transaction')

    def get_balance(self):
        return sum([
            transaction.amount
            for transaction in self.transactions
            # I don't have to use it but I want to prepare for removing wallet_id
            if transaction.subwallet in self.subwallets
        ])

    def get_currency(self):
        currency = db.session.query(CurrencyOfficialAbbr).join(Wallet,
            CurrencyOfficialAbbr.id == self.currency
        ).first()
        return currency.abbr

    def add_subwallet(self):
        pass


class Subwallet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'))
    name = db.Column(db.String(64), index=True)

    transactions = db.relationship('Transaction', backref='subwallet')
    # currencies = db.relationship('Transaction', back_populates='sub_wallet')

    def get_balance(self):
        return sum([
            transaction.amount
            for transaction in self.transactions
        ])


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallet.id'))
    subwallet_id = db.Column(db.Integer, db.ForeignKey('subwallet.id'))
    currency_id = db.Column(db.Integer, db.ForeignKey('currency_official_abbr.id'))
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    type = db.Column(db.String(64))
    amount = db.Column(db.Float(precision='2'))
    description = db.Column(db.String(256))

    expenses = db.relationship('Expense', backref='transaction')


# class AssociationSubwalletCurrency(db.Model):
#     subwallet_id = db.Column(db.Integer, db.ForeignKey('subwallet.id'), primary_key=True)
#     currency_id = db.Column(db.Integer, db.ForeignKey('currency_official_abbr.id'), primary_key=True)
#     balance = db.Column(db.Float)



@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
