import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from eTracker.models import User



class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_pswd = PasswordField('Repeat Password', [DataRequired(), EqualTo('password')])# consider InputRequired()
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('This email already has been used. Please use a different one.')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Already used. Please use a different username.')

    def validate_password(self, password):
        match = re.match(r'(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])\w{6,}', password.data)
        if match is None:
            raise ValidationError('Password should contain upper- and lowercase, '
                                'number and should be at least 6 characters.')
