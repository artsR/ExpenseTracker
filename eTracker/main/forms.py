import datetime
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
        StringField, DateField, FloatField, SubmitField, TextAreaField,
        HiddenField, SelectField, RadioField, SelectMultipleField
)
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms_components import ColorField
from wtforms.validators import DataRequired, ValidationError, Length, Optional
from wtforms.fields import html5
from eTracker.models import Currency


# Monkeypatch for https://github.com/wtforms/wtforms/issues/373:
import wtforms_sqlalchemy.fields as f
def get_pk_from_identity(obj):
    cls, key = f.identity_key(instance=obj)[:2]
    return ':'.join(f.text_type(x) for x in key)
f.get_pk_from_identity = get_pk_from_identity



class AddExpenseForm(FlaskForm):
    wallet_id = SelectField('Wallet', [DataRequired()])
    subwallet_id = SelectField('Subwallet', [DataRequired()])
    expenseDate = DateField('ExpenseDate', [DataRequired()])
    product = StringField('Product', [DataRequired()])
    quantity = FloatField('quantity')
    price = FloatField('price', [DataRequired()])
    currency = SelectField('currency', validators=[DataRequired()], coerce=int)
    category = StringField('Category')
    freq = SelectField('Freq', default='daily', choices=[
        ('daily', 'daily'), ('monthly', 'monthly'),
        ('a_few_times', 'a few times'), ('annually', 'annually'),
    ])
    submit = SubmitField('Add Expense')


class UploadForm(FlaskForm):
    customFile = FileField(validators=[FileRequired(),
                            FileAllowed(['png', 'jpg', 'jpeg'])])
    submit = SubmitField('Upload')


class WalletForm(FlaskForm):
    wallet_name = StringField('Name', [DataRequired()])
    wallet_color = StringField('Color', [DataRequired()])
    currency = SelectField('Currency', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Create')


class TransactionForm(FlaskForm):
    transaction_id = HiddenField('transaction_id')
    date = html5.DateField('Date', validators=[Optional()])
    wallet = QuerySelectField(
        query_factory=lambda:current_user.wallets, get_label='name',
        label='Wallet',
    )
    subwallet = SelectField('Subwallet', coerce=int,
                            validators=[DataRequired()])
    currency = StringField('Currency', render_kw={'disabled': True})
    amount = html5.DecimalField('Amount', validators=[DataRequired()])
    category = QuerySelectField(
        query_factory=lambda:current_user.categories, get_label='name',
        label='Category',
    )
    description = TextAreaField('Description', validators=[Length(min=0, max=150)])
    submit = SubmitField('Update')


class WalletsSubwallets(FlaskForm):
    subwallet_wallets = QuerySelectField(
        query_factory=lambda:current_user.wallets, get_label='name',
        label='Wallet',
    )
    subwallet_subwallets = QuerySelectField(
        query_factory=lambda:current_user.subwallets, get_label='name',
        label='Subwallet',
    )


class FiltersForm(FlaskForm):
    date_start = html5.DateField('Date Start', validators=[Optional()])
    date_end = html5.DateField('Date End', validators=[Optional()])
    amount_min = html5.DecimalField('Amount_min', validators=[Optional()])
    amount_max = html5.DecimalField('Amount_max', validators=[Optional()])
    currencies = QuerySelectMultipleField(
        query_factory=lambda:Currency.query, get_label='abbr',
        label='Currencies',
    )
    wallets = QuerySelectMultipleField(
        query_factory=lambda:current_user.wallets, get_label='name',
        label='Wallets',
    )
    subwallets = QuerySelectMultipleField(
        query_factory=lambda:current_user.subwallets, get_label='name',
        label='Subwallets',
    )
    categories = QuerySelectMultipleField(
        query_factory=lambda:current_user.categories, get_label='name',
        label='Categories',
    )
    submit = SubmitField('Apply')


class TransactionForm_(FlaskForm):
    type = SelectField('Type', choices=[('Expense', 'EXPENSE'), ('Income', 'INCOME')])
    #wallet_id #DataRequired SelectField allow_blank=False
    #currency_wallet disabled
    #subwallet_id #optional SelectField allow_blank=True
    #currency_subwallet SelectField
    # maybe I should change border of <form> green/red - depending on type.
    amount = FloatField('Amount')
    description = TextAreaField('Description', validators=[Length(min=0, max=150)])
