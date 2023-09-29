import math
import umbrella.db_interface as db_interface
from umbrella import login_manager
from flask_login import UserMixin
import datetime


class DBModel():
    table_name = ""
    is_deleted = False
    id = 0

    def set_id(self, new_id):
        if not isinstance(new_id, int):
            raise ValueError("id param not an int.")
        self.id = new_id


@login_manager.user_loader
def load_user(user_id):
    return db_interface.read_rows('profile', cond=('id', user_id))


class User(DBModel, UserMixin):
    db_columns = [
        ("id", "serial", "PRIMARY KEY"),
        ("username", "varchar(255)", "UNIQUE NOT NULL"),
        ("email", "varchar(255)", "UNIQUE NOT NULL"),
        ("password", "varchar(255)", "UNIQUE NOT NULL"),
        ("bio", "varchar(511)"),
        ("created_at", "timestamp", "DEFAULT current_timestamp NOT NULL"),
        ("is_deleted", "boolean"),
    ]

    table_name = "profile"

    def __init__(self, username=None, password=None, email=None, bio=None):
        self.username = username
        self.password = password
        self.email = email
        self.bio = bio
        self.created_at = datetime.datetime.now()

    def __str__(self):
        return self.username.get_content() + ' User'

    def set_date(self, date):
        if date != datetime.datetime:
            raise ValueError("date param not a datetime object.")
        self.created_at = date

    def query_users(self, user_filter=None):
        if user_filter:
            row = db_interface.read_rows('profile', cond=user_filter)

            id, username, email, password, bio, join_date, _ = row[0]

            user = User(username, password, email, bio)
            user.set_date(join_date)
            user.set_id(id)

            return user

        rows = db_interface.read_rows('profile')
        users = []
        for r in rows:
            id, username, email, _, bio, join_date = r

            user = User(username, None, email, bio)
            user.set_date(join_date)
            user.set_id(id)

            users.append(user)

        return users


class Post(DBModel):
    db_columns = [
        ("id", "serial", "PRIMARY KEY"),
        ("title", "varchar(255)", "UNIQUE NOT NULL"),
        ('"content"', "text", "NOT NULL"),
        ("created_at", "timestamp", "DEFAULT current_timestamp NOT NULL"),
        ("view_count", "bigserial", "NOT NULL"),
        ("author_id", "int", "REFERENCES profile(id)"),
        ("category_id", "int", "REFERENCES category(id)"),
        ("is_deleted", "boolean"),
    ]

    table_name = "post"

    def __init__(self, title=None, content=None, view_count=None, author=None, category=None):
        self.title = title
        self.content = content
        self.view_count = view_count
        self.author = author
        self.category = category
        self.created_at = datetime.datetime.now()

    def __str__(self):
        return self.title

    def set_date(self, date):
        if date != datetime.datetime:
            raise ValueError("date param not a datetime object.")
        self.created_at = date

    def _populate_post(self, row):
        id, title, content, created_at, view_count, author_id, category_id, _ = row

        user = User().query_users(('id', author_id))[0]
        cat = Category().query_categories(('id', category_id))[0]

        post = Post(title, content, view_count, user, cat)
        post.set_date(created_at)
        post.set_id(id)

        return post

    def _get_posts(self, limit, post_filter=None):
        if post_filter:
            rows = db_interface.read_rows(self.table_name, cond=post_filter, limit=limit)
            posts = []

            for r in rows:
                post = self._populate_post(r)
                posts.append(post)

            return posts

        rows = db_interface.read_rows(self.table_name, limit=limit)
        posts = []

        for r in rows:
            post = self._populate_post(r)
            posts.append(post)

        return posts

    def query_posts(self, post_filter=None, limit=20):
        if post_filter:
            self._get_posts(limit, post_filter)

        posts = self._get_posts(limit)
        return posts


class Pagination():
    def __init__(self, items: list, per_page=10, page=0):
        self.items = items

        if per_page == 0:
            raise ValueError("per_page cannot be zero.")
        self.per_page = per_page

        self.page = page

    @staticmethod
    def get_last_page(items_len, per_page):
        div_result = items_len / per_page
        if div_result > 1:
            return math.ceil(div_result)
        else:
            return math.floor(div_result)


def get_paginated_items(items: list, per_page=10, page=0):
    new_items = []
    tally = 0

    if page > Pagination.get_last_page(len(items), per_page):
        raise ValueError("Given page argument is larger than the last possible page.")

    if page > 0:
        starting_pos = page * per_page

        for i in items[starting_pos:]:
            if tally > per_page:
                break
            new_items.append(i)
            tally += 1

    return Pagination(new_items, per_page, page)


class Comment(DBModel):
    db_columns = [
        ("id", "serial", "PRIMARY KEY"),
        ('"content"', "text", "NOT NULL"),
        ("created_at", "timestamp", "DEFAULT current_timestamp NOT NULL"),
        ("author_id", "int", "REFERENCES profile(id)"),
        ("post_id", "int", "REFERENCES post(id)"),
        ("is_deleted", "boolean"),
    ]

    table_name = "comment"

    def __init__(self, content=None, author=None, post_id=None):
        self.content = content
        self.created_at = datetime.datetime.now()
        self.post_id = post_id
        self.author = author

    def __str__(self):
        return self.id

    def set_date(self, date):
        if date != datetime.datetime:
            raise ValueError("date param not a datetime object.")
        self.created_at = date

    def query_comments(self, comment_filter=None):
        if comment_filter:
            row = db_interface.read_rows(self.table_name, cond=comment_filter)

            id, content, created_at, author_id, post_id, _ = row[0]
            author = User().query_users(('id', author_id))[0]

            com = Comment(content, author, post_id)
            com.set_date(created_at)
            com.set_id(id)

            return com

        rows = db_interface.read_rows(self.table_name)
        coms = []
        for r in rows:
            id, content, created_at, author_id, post_id, _ = r

            com = Comment(content, author_id, post_id)
            com.set_date(created_at)
            com.set_id(id)

            coms.append(com)

        return coms


class PostComment():
    def __init__(self, title, content, author_id, post_id, created_at):
        self.comments = self._query_post_comments()

        self.post = Post(title, content, author_id)
        self.post.set_id(post_id)
        self.post.set_date(created_at)

    def _query_post_comments(self):
        return Comment().query_comments(('post_id', self.post.id))


class Category(DBModel):
    db_columns = [
        ("id", "serial", "PRIMARY KEY"),
        ("title", "varchar(255)", "UNIQUE NOT NULL"),
        ("description", "varchar(255)"),
        ("post_count", "bigserial", "NOT NULL"),
        ("is_deleted", "boolean"),
    ]

    table_name = "category"

    def __init__(self, title=None, desc=None, post_count=None):
        self.id = 0
        self.title = title
        self.desc = desc
        self.post_count = post_count

    def __str__(self):
        return self.title

    def query_categories(self, ind_cat_filter=None):
        if ind_cat_filter:
            rows = db_interface.read_rows(self.table_name, cond=ind_cat_filter)

            id, title, content, desc, post_count, _ = rows[0]

            cat = Category(title, desc, post_count)
            cat.set_id(id)

            return cat

        rows = db_interface.read_rows(self.table_name)
        cats = []
        for r in rows:
            id, title, content, desc, post_count, _ = r

            cat = Category(title, desc, post_count)
            cat.set_id(id)

            cats.append(cat)

        return cats
