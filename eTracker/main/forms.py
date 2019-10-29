from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import ( StringField, DateField, FloatField, DecimalField,
                SubmitField, SelectField, RadioField, SelectMultipleField )
from wtforms.validators import DataRequired



class AddExpenseForm(FlaskForm):
    expenseDate = DateField('ExpenseDate', [DataRequired()] )
    product = StringField('Product', [DataRequired()] )
    quantity = FloatField('quantity')
    price = DecimalField('price', [DataRequired()] )
    currency = SelectField('currency', default='pln', validators=[DataRequired()])
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
    abbr = StringField('Abbr', [DataRequired()])
    name = StringField('Name')
    submit = SubmitField('Add')


class FiltersForm(FlaskForm):
    beforeDate = DateField('beforeDate')
    afterDate = DateField('afterDate')
    category = SelectMultipleField('categories')
    freq = SelectMultipleField('freq', choices=[])
    submit = SubmitField('Apply')
