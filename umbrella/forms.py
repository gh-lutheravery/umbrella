from flask_wtf import FlaskForm
from flask_login import current_user
from flask_ckeditor import CKEditorField
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
import umbrella.db_interface as db_interface


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    bio = StringField('Bio', validators=[Length(max=250)])
    submit = SubmitField('Sign up')

    def validate_username(self, username):
        rows = db_interface.read_rows('profile', cond=('username', username.data))

        if len(rows) != 0:
            raise ValidationError('An account with that username exists; choose a different one.')

    def validate_email(self, email):
        rows = db_interface.read_rows('profile', cond=('email', email.data))

        if len(rows) != 0:
            raise ValidationError('An account with that email exists; choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')




class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = StringField('Bio', validators=[Length(min=2, max=250)])
    submit = SubmitField('Update')

    def validate_username(self, username):
        # if username was changed
        if username.data != current_user.username:
            rows = db_interface.read_rows('profile', cond=('username', username.data))

            if len(rows) != 0:
                raise ValidationError('An account with that username exists; choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            rows = db_interface.read_rows('profile', cond=('email', email.data))

            if len(rows) != 0:
                raise ValidationError('An account with that email exists; choose a different one.')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=2, max=100)])
    content = CKEditorField('Content', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Post')

    def validate_title(self, title):
        rows = db_interface.read_rows('post', cond=('title', title.data))

        if len(rows) != 0:
            raise ValidationError('A post with that title exists; please choose a different one.')

    def validate_category(self, category):
        rows = db_interface.read_rows('category', cond=('title', category.data))

        if len(rows) == 0:
            raise ValidationError('A category with that title does not exist; choose a different one.')

class CommentForm(FlaskForm):
    content = StringField('Content', validators=[DataRequired()])
    submit = SubmitField()
