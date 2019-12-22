from flask import render_template, redirect, url_for, flash
from flask import request
from flask_login import current_user, login_user, logout_user, login_required
from eTracker import db
from eTracker.models import User
from eTracker.auth import bp
from eTracker.auth.forms import LoginForm, RegistrationForm



# The prefix '/auth' is defined on registration in eTracker/__init__.py.

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
@login_required
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
        new_user.add_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('You Signed Up succesfully. Now you can login to our service.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)
