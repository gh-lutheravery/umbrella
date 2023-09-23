import umbrella.db_interface as db_interface
from umbrella import login_manager
from flask_login import UserMixin
import datetime



class DBModel():
    table_name = ""
    is_deleted = False


@login_manager.user_loader
def load_user(user_id):
    return read_rows('profile', ('id', user_id))


def read_rows(table_name, cond=None):
    if cond:
        query = "SELECT * FROM " + table_name + " WHERE {} = %s AND is_deleted = False"
        params = [cond[1]]
        field_param = cond[0]
        rows = db_interface.run_query(query, params, field_param)
        return rows

    query = "SELECT * FROM " + table_name + " WHERE is_deleted = False"
    rows = db_interface.run_query(query)
    return rows


def insert_table(table_name, form_obj, default_id_name=None):
    # Extract attribute names and values from the object
    attributes = get_obj_attrs(form_obj)

    # if id in table autoincrements
    if default_id_name:
        attributes.append(default_id_name)
        attribute_values = [getattr(form_obj, attr) for attr in attributes]
        attribute_values.append("DEFAULT")
    else:
        attribute_values = [getattr(form_obj, attr) for attr in attributes]

    column_str = ', '.join(attributes)
    param_str = ('%s,' * len(attribute_values)).rstrip(',')

    insert_query = """
            INSERT INTO """ + table_name + """ (""" + column_str + """)
            VALUES (""" + param_str + """);
            """

    db_interface.run_query(insert_query, attribute_values)


def get_obj_attrs(obj):
    attrs = []
    for attr in dir(obj):
        if not callable(getattr(obj, attr)) and not attr.startswith("__"):
            attrs.append(attr)

    return attrs


def update_row(form_obj, table_name, cond_filter, soft_delete_flag=None):
    if soft_delete_flag:
        update_query = f"""
            UPDATE {table_name}
            SET is_deleted = %s
            WHERE {cond_filter[0]} = %s;
            """

        params = [soft_delete_flag, cond_filter[1]]

        db_interface.run_query(update_query, params)

    else:
        # Extract attribute names and values from the object
        attributes = get_obj_attrs(form_obj)
        attribute_values = [getattr(form_obj, attr) for attr in attributes]

        # Build the SET clause for the UPDATE query
        set_clauses = [f"{attr} = %s" for attr in attributes]
        set_clause_str = ", ".join(set_clauses)

        # Define the UPDATE query
        update_query = f"""
        UPDATE {table_name}
        SET {set_clause_str}
        WHERE {cond_filter[0]} = %s;
        """

        params = [attribute_values + [getattr(form_obj, cond_filter[1])]]
        db_interface.run_query(update_query, params)


def soft_delete(table_name, cond_filter):
    update_row(None, table_name, cond_filter, soft_delete_flag=True)


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

    table_name = "user"

    def __init__(self, username=None, password=None, email=None, bio=None):
        self.id = 0
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

    def set_id(self, id):
        if id != int:
            raise ValueError("date param not a datetime object.")
        self.id = id

    def query_users(self, user_filter=None):
        if user_filter:
            row = read_rows('profile', user_filter)

            id, username, email, password, bio, join_date, _ = row[0]

            user = User(username, password, email, bio)
            user.set_date(join_date)
            user.set_id(id)

            return user

        rows = read_rows('profile')
        users = []
        for r in rows:
            id, username, email, _, bio, join_date = r

            user = User(username, None, email, bio)
            user.set_date(join_date)
            user.set_id(id)

            users.append(user)

        return users


    def create_user_table(self):
        query = "CREATE TABLE IF NOT EXISTS user (" \
                "id, serial, PRIMARY KEY" \
                "username, varchar(255), NOT NULL" \
                "email, varchar(255), UNIQUE NOT NULL" \
                "password, varchar(255), UNIQUE NOT NULL" \
                "bio, varchar(511)" \
                "created_at, timestamp, DEFAULT current_timestamp NOT NULL" \
                "is_deleted, boolean" \
                ");"

        db_interface.run_query(query)


class Post(DBModel):
    db_columns = [
        ("id", "serial", "PRIMARY KEY"),
        ("title", "varchar(255)", "UNIQUE NOT NULL"),
        ("content", "text", "NOT NULL"),
        ("created_at", "timestamp", "DEFAULT current_timestamp NOT NULL"),
        ("view_count", "bigint", "NOT NULL"),
        ("author_id", "varchar(255)", "NOT NULL"),
        ("is_deleted", "boolean"),
    ]

    table_name = "post"

    def __init__(self, title=None, content=None, view_count=None, author_id=None):
        self.id = 0
        self.title = title
        self.content = content
        self.view_count = view_count
        self.author_id = author_id
        self.created_at = datetime.datetime.now()

    def __str__(self):
        return self.title

    def set_date(self, date):
        if date != datetime.datetime:
            raise ValueError("date param not a datetime object.")
        self.created_at = date

    def set_id(self, id):
        if id != int:
            raise ValueError("date param not a datetime object.")
        self.id = id

    def query_posts(self, post_filter=None):
        if post_filter:
            row = read_rows(self.table_name, post_filter)

            id, title, content, created_at, view_count, author_id, _ = row[0]

            post = Post(title, content, view_count, author_id)
            post.set_date(created_at)
            post.set_id(id)

            return post

        rows = read_rows(self.table_name)
        posts = []
        for r in rows:
            id, title, content, created_at, view_count, author_id, _ = r

            post = Post(title, content, view_count, author_id)
            post.set_date(created_at)
            post.set_id(id)

            posts.append(post)

        return posts

    def create_post_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS post (
            id serial PRIMARY KEY,
            title varchar(255) NOT NULL,
            content text NOT NULL,
            created_at timestamp DEFAULT current_timestamp NOT NULL,
            view_count bigint NOT NULL,
            author_id varchar(255) NOT NULL,
            is_deleted boolean
        );
        """

        db_interface.run_query(query)


class Comment(DBModel):
    db_columns = [
        ("id", "serial", "PRIMARY KEY"),
        ("content", "text", "NOT NULL"),
        ("created_at", "timestamp", "DEFAULT current_timestamp NOT NULL"),
        ("author_id", "varchar(255)", "NOT NULL"),
        ("post_id", "varchar(255)", "NOT NULL"),
        ("is_deleted", "boolean"),
    ]

    table_name = "comment"

    def __init__(self, content=None, author_id=None, post_id=None):
        self.id = 0
        self.content = content
        self.created_at = datetime.datetime.now()
        self.post_id = post_id
        self.author_id = author_id

    def __str__(self):
        return self.id

    def set_date(self, date):
        if date != datetime.datetime:
            raise ValueError("date param not a datetime object.")
        self.created_at = date

    def set_id(self, id):
        if id != int:
            raise ValueError("date param not a datetime object.")
        self.id = id

    def query_comments(self, comment_filter=None):
        if comment_filter:
            row = read_rows(self.table_name, comment_filter)

            id, content, created_at, author_id, post_id, _ = row[0]

            com = Comment(content, author_id, post_id)
            com.set_date(created_at)
            com.set_id(id)

            return com

        rows = read_rows(self.table_name)
        coms = []
        for r in rows:
            id, content, created_at, author_id, post_id, _ = r

            com = Comment(content, author_id, post_id)
            com.set_date(created_at)
            com.set_id(id)

            coms.append(com)

        return coms

    def create_comment_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS comment (
            id serial PRIMARY KEY,
            content text NOT NULL,
            created_at timestamp DEFAULT current_timestamp NOT NULL,
            author_id varchar(255) NOT NULL,
            post_id varchar(255) NOT NULL,
            is_deleted boolean
        );
        """

        db_interface.run_query(query)


class PostComment():
    def __init__(self, title, content, author_id, post_id, created_at):
        self.comments = self._query_post_comments()

        self.post = Post(title, content, author_id)
        self.post.set_id(post_id)
        self.post.set_date(created_at)

    def _query_post_comments(self):
        return Comment().query_comments(('post_id', self.post.id))
