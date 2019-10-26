from hashlib import  md5
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from eTracker import db, login



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(64), index=True, unique=True)
    pswd_hash = db.Column(db.String(128))
    expenses = db.relationship('Expense', backref='user')
    currency = db.relationship('Currency', backref='user')

    def add_password(self, password):
        self.pswd_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pswd_hash, password)

    def get_groups(self, group):
        return Expense.query.filter(Expense.user == self).group_by(
                Expense.category)

    def spendings(self):
        return db.session.query(Expense.id,
                                Expense.expenseDate, Expense.product,
                                Expense.category, Expense.freq,
                                Expense.quantity, Expense.price,
                                Expense.currency).filter(
                                Expense.user == self)

    def __repr__(self):
        return f"<User(id= {self.id}, username = {self.username}, email = {self.email})"


class Expense(db.Model):
    id = db.Column(db.Integer, db.Sequence('expense_id_seq'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    expenseDate = db.Column(db.Date, index=True)
    product = db.Column(db.String(140), index=True)
    category = db.Column(db.String(140), index=True)
    freq = db.Column(db.String(64))#list
    quantity = db.Column(db.Float())
    price = db.Column(db.Float(precision='2'))
    currency = db.Column(db.String(10))#list

    def __repr__(self):
        return f"<Expense {self.id} {self.product} {self.category} {self.price}"


class Currency(db.Model):
    abr = db.Column(db.String(10), unique=True, index=True, primary_key=True)
    name = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))




@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
