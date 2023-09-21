from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from umbrella.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Password', validators=[DataRequired(), EqualTo('password')])
    bio = StringField('Username', validators=[Length(min=2, max=150)])
    submit = SubmitField('Sign up')

    def validate_username(self, username):
        user = User.query_users(User(), 'username', 'ASC', username)
        if user:
            raise ValidationError('An account with that username exists; choose a different one.')

    def validate_email(self, email):
        user = User.query_users(User(), 'email', 'ASC', email)
        if user:
            raise ValidationError('An account with that email exists; choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

