from flask import render_template, url_for, flash, redirect, request, abort
from umbrella import app, bcrypt
from umbrella.forms import RegistrationForm, LoginForm, UpdateProfileForm, PostForm, CommentForm
import umbrella.models as models
from flask_login import login_user, logout_user, login_required, current_user


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
            user = models.User(form.username.data, hashed_password_str, form.email.data)
        else:
            user = models.User(form.username.data, hashed_password_str, form.email.data, form.bio.data)

        models.insert_table('profile', user, default_id_name='id')
        flash(form.username.data + ' account has been created.')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = models.read_rows('profile', ('email', form.email.data))
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('You are now logged in.')
            return redirect(url_for('home'))
        else:
            flash('Login was unsuccessful; please check your email and password.')

    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        models.update_row(form, 'profile', ('id', current_user.id))
        flash('Profile has been updated.')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('profile.html', title='Profile', form=form)

@app.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = models.Post(form.title.data, form.content.data, 0, current_user.id)
        models.insert_table('profile', post, default_id_name='id')
        flash('Post has been created.')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form)

@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        models.insert_table('comment', form, 'id')
        flash('Comment has been posted.')
        return redirect(url_for('post', post_id=post_id))

    post = read_or_abort('post', ('id', post_id))
    post_comment = models.PostComment(post.title,
                                      post.content,
                                      post.author_id,
                                      post.id,
                                      post.created_at
                                      )

    return render_template('post.html', title=post_comment.post.title, post=post_comment)

def read_or_abort(table_name, filter):
    post = models.read_rows('post', filter)
    if len(post) == 0:
        abort(404, description="Post not found")
    return post

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = read_or_abort('post', ('id', post_id))
    if post.author_id != current_user.id:
        # user is forbidden
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        models.update_row(form, 'post', ('id', post_id))
        flash('Post has been updated.')
        return redirect(url_for('post', post_id=post_id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('update_post.html', title='Update Post', form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = read_or_abort('post', ('id', post_id))
    if post.author_id != current_user.id:
        # user is forbidden
        abort(403)
    models.soft_delete('post', ('id', post_id))
    flash('Post has been deleted.')
    return redirect(url_for('home'))

