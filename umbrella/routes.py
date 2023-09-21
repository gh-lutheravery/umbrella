from flask import render_template, url_for, flash, redirect
from umbrella import app, bcrypt
from umbrella.forms import RegistrationForm, LoginForm
from umbrella.models import User

@app.route("/")
@app.route("/home")
def home():
    return "<h1>Home Page</h1>"


@app.route("/about")
def about():
    return "<h1>About Page</h1>"

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        hashed_password_str = hashed_password.decode('utf-8')
        if not form.bio:
            user = User(form.username.data, hashed_password_str, form.email.data)
        else:
            user = User(form.username.data, hashed_password_str, form.email.data, form.bio.data)
        user.insert_user_table()
        flash(form.username.data + ' account has been created.')

    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == '' and form.password.data == '':
            flash('You are now logged in.')
        else:
            flash('Login is unsuccessful.')


    return render_template('login.html', title='Login', form=form)