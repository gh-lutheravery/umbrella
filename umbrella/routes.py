import copy

from flask import render_template, url_for, flash, redirect, request, abort
from umbrella import app, bcrypt
from umbrella.forms import RegistrationForm, LoginForm, UpdateProfileForm, PostForm, CommentForm
import umbrella.models as models
import umbrella.db_interface as db_interface
from flask_login import login_user, logout_user, login_required, current_user
from flask_paginate import Pagination


@app.route("/")
@app.route("/home")
def home():
    cats = models.Category().query_categories()
    category_id = request.args.get('category', default=None)
    if category_id:
        posts = models.Post().query_posts(limit=20, post_filter=('category_id', category_id))
        return render_template('home.html', posts=posts, cats=cats)

    posts = models.Post().query_posts(limit=20)
    return render_template('home.html', posts=posts, cats=cats)


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

        db_interface.insert_table('profile', user)
        flash(f'"{form.username.data}" account has been created.')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        users = models.User().query_users(('email', form.email.data))
        if len(users) != 0 and bcrypt.check_password_hash(users[0].password, form.password.data):
            login_user(users[0], remember=form.remember.data)
            flash('You are now logged in.')
            return redirect(url_for('home'))
        else:
            flash('Login was unsuccessful; please check your email and password.')

    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/profile/<int:profile_id>")
def profile(profile_id):
    profiles = models.User().query_users(('id', profile_id))
    if len(profiles) == 0:
        abort(404)
    profile = profiles[0]
    return render_template('profile.html', title='Profile', profile=profile)


@app.route("/profile/update", methods=['GET', 'POST'])
@login_required
def update_profile():
    form = UpdateProfileForm()

    if form.validate_on_submit():
        if form.bio:
            user = copy.deepcopy(current_user)
            user.username = form.username.data
            user.email = form.email.data
            user.bio = form.bio.data

        else:
            user = copy.deepcopy(current_user)
            user.username = form.username.data
            user.email = form.email.data

        db_interface.update_row_obj(user, 'profile', ('id', current_user.id))
        flash('Profile has been updated.')
        return redirect(url_for('profile', profile_id=current_user.id))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio

    return render_template('update_profile.html', title='Profile', form=form)

@app.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = models.Post(form.title.data, form.content.data, 0, current_user.id)
        post.author_id = current_user.id

        # can only be one element since titles have unique constraint
        cat = models.Category().query_categories(('title', form.category.data))[0]
        post.category_id = cat.id

        db_interface.insert_table(post.table_name, post)

        # get category of post and increment the categories' post_count
        db_interface.update_row(['post_count'], [], cat.table_name, ('id', cat.id),
                                default_col='post_count')

        flash('Post has been created.')
        return redirect(url_for('home'))

    return render_template('create_post.html', title='New Post', form=form)

@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    form = CommentForm()
    post_comment = models.PostComment(post_id)

    if form.validate_on_submit():
        if current_user.is_authenticated:
            com = models.Comment(form.content.data, current_user, post_id)
            com.author_id = current_user.id
            db_interface.insert_table('comment', com)
            flash('Comment has been posted.')
            return redirect(url_for('post', post_id=post_id))

        flash('You must be logged in to comment.')
        return redirect(url_for('post', post_id=post_id))

    return render_template('post.html', title=post_comment.post.title,
                           post_comment=post_comment, form=form)

def read_or_abort_p(filter, use_like=False):
    if use_like:
        posts = models.Post().query_posts(filter, use_like=True)
    else:
        posts = models.Post().query_posts(filter)

    if len(posts) == 0:
        abort(404, description="Post not found")
    return posts

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = read_or_abort_p(('id', post_id))[0]

    if post.author_id != current_user.id:
        # user is forbidden
        abort(403)
    form = PostForm()

    if form.validate_on_submit():
        new_post = post
        new_post.title = form.title.data
        new_post.content = form.content.data

        db_interface.update_row_obj(new_post, post.table_name, ('id', post_id))
        flash('Post has been updated.')
        return redirect(url_for('post', post_id=post_id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('create_post.html', title='Update Post', form=form)

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = read_or_abort_p(('id', post_id))[0]
    if post.author_id != current_user.id:
        # user is forbidden
        abort(403)

    db_interface.soft_delete('post', ('id', post_id))
    flash('Post has been deleted.')
    return redirect(url_for('home'))


@app.route("/search-results")
def search():
    search_query = request.args.get('query', default=None)
    if not(search_query):
        abort(400)
    page = request.args.get('page', default=1, type=int)

    posts = read_or_abort_p(('title', search_query), use_like=True)

    pagination = Pagination(page=page, per_page=10, total=len(posts))

    return render_template('search.html',
                           title=search_query + ' Search Results',
                           posts=posts, pagination=pagination, query=search_query)
