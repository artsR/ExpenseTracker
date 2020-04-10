from flask import render_template, redirect, url_for, flash
from flask import request
from flask_login import current_user, login_user, logout_user, login_required
from eTracker import db
from eTracker.models import User
from eTracker.auth import bp
from eTracker.auth.email import send_password_reset_link
from eTracker.auth.forms import (
    LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
)



@bp.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        flash('You are already logged in', 'info')
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid email address or password.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        flash('Welcome in your account.', 'success')

        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    return render_template('auth/login.html', form=form)


@bp.route('/logout')
def logout():

    logout_user()
    flash('You was logged out succesfully', 'warning')

    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data.lower(), email=form.email.data.lower())
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('You Signed Up succesfully. Now you can login to our service.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            send_password_reset_link(user)
        flash('Check email for further instuctions', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password_request.html', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for('main.index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been changed succesfully', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)
