from flask import render_template, url_for, flash, redirect
from umbrella import app
from umbrella.forms import RegistrationForm, LoginForm
from umbrella.models import User

@app.route("/")
@app.route("/home")
def home():
    return "<h1>Home Page</h1>"


@app.route("/about")
def about():
    return "<h1>About Page</h1>"
