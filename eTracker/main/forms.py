from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import ( StringField, DateField, FloatField, DecimalField,
                SubmitField, SelectField )
from wtforms.validators import DataRequired




class AddExpenseForm(FlaskForm):
    expenseDate = DateField('ExpenseDate', [DataRequired()] )
    product = StringField('Product', [DataRequired()] )
    quantity = FloatField('quantity')
    price = DecimalField('price', [DataRequired()] )
    currency = SelectField('currency', default='pln',
                    choices=[ ('pln', 'PLN'), ('lv', 'LV'), ('eur', 'EUR'), ('usd', 'USD') ])
    category = StringField('Category')
    freq = SelectField('Freq', default='daily',
                    choices=[ ('daily', 'daily'), ('monthly', 'monthly'),
                    ('a_few_times', 'a few times'), ('annually', 'annually') ])
    submit = SubmitField('Add Expense')


class UploadForm(FlaskForm):
    customFile = FileField(validators=[FileRequired(),
                            FileAllowed(['png', 'jpg', 'jpeg'])])
    submit = SubmitField('Upload')


class CurrencyForm(FlaskForm):
    abv = StringField('Abv', [DataRequired()])
    name = StringField('Name')
