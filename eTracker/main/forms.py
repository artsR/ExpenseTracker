from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
        StringField, DateField, FloatField, DecimalField, SubmitField,
        SelectField, RadioField, SelectMultipleField, TextAreaField
)
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms_components import ColorField
from wtforms.validators import DataRequired, ValidationError, NumberRange, Length
from eTracker.models import CurrencyOfficialAbbr

# Monkeypatch for https://github.com/wtforms/wtforms/issues/373:
import wtforms_sqlalchemy.fields as f
def get_pk_from_identity(obj):

    cls, key = f.identity_key(instance=obj)[:2]
    return ':'.join(f.text_type(x) for x in key)
f.get_pk_from_identity = get_pk_from_identity



class AddExpenseForm(FlaskForm):
    wallet = SelectField('Wallet', [DataRequired()])
    subwallet = SelectField('Subwallet', [DataRequired()])
    expenseDate = DateField('ExpenseDate', [DataRequired()])
    product = StringField('Product', [DataRequired()])
    quantity = FloatField('quantity')
    price = DecimalField('price', [DataRequired()])
    currency = SelectField('currency', default='pln', validators=[DataRequired()])
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


class CurrencyForm(FlaskForm):
    abbr = SelectField('Abbr', [DataRequired()], default='PLN')
    name = StringField('Name')
    submit = SubmitField('Add')


class FiltersForm(FlaskForm):
    beforeDate = DateField('beforeDate')
    afterDate = DateField('afterDate')
    product = StringField('product')
    category = SelectMultipleField('categories')
    freq = SelectMultipleField('freq', choices=[])
    submit = SubmitField('Apply')


class WalletForm(FlaskForm):
    name = StringField('Name', [DataRequired()])
    color = StringField('Color', [DataRequired()])
    balance = FloatField('Balance', [NumberRange(min=0.0)])
    currency = SelectField('Currency', validators=[DataRequired()], coerce=int)
    # currency = QuerySelectField(
    #     label='Currency',
    #     validators=[DataRequired()],
    #     query_factory=lambda: CurrencyOfficialAbbr.query,
    #     get_pk=f.get_pk_from_identity,
    #     get_label='abbr',
    #     allow_blank=False, # choising blank option now (False) is not possible.
    # )
    # QuerySelectField(query_factory=Area.objects.all,
    #                         get_pk=lambda a: a.id,
    #                         get_label=lambda a: a.name)
    submit = SubmitField('Create')


class SubwalletForm(FlaskForm):
    wallet = SelectField('Wallet')
    name = StringField #introduce new or choose from existing


class TransactionForm(FlaskForm):
    type = SelectField('Type', choices=[('Expense', 'EXPENSE'), ('Income', 'INCOME')])
    #wallet_id #DataRequired SelectField allow_blank=False
    #currency_wallet disabled
    #subwallet_id #optional SelectField allow_blank=True
    #currency_subwallet SelectField
    # maybe I should change border of <form> green/red - depending on type.
    amount = FloatField('Amount')
    description = TextAreaField('Description', validators=[Length(min=0, max=150)])


class TransferForm(FlaskForm):
    wallet_from = SelectField('Wallet_from')
    subwallet_from = SelectField('Subwallet_from')
    wallet_to = SelectField('Wallet_to')
    subwallet_to = SelectField('Subwallet_to')
    amount = FloatField('Amount')
