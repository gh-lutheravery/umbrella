import umbrella.db_interface as db_interface
from umbrella import login_manager
from flask_login import UserMixin
import datetime



class DBModel():
    table_name = ""
    is_deleted = False


@login_manager.user_loader
def load_user(user_id):
    return User.query_users(User(), user_id)


def read_rows(self, table_name, cond=None):
    if cond:
        query = "SELECT * FROM " + table_name + " WHERE {} = %s AND is_deleted = False"
        params = [cond[1]]
        field_param = cond[0]
        rows = db_interface.run_query(query, params, field_param)
        return rows

    query = "SELECT * FROM " + table_name + " WHERE is_deleted = False"
    rows = db_interface.run_query(query)
    return rows


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
        self.join_date = datetime.datetime.now()

    def __str__(self):
        return self.username.get_content() + ' User'


    def query_users(self, user_filter=None):
        if user_filter:
            row = read_rows('profile', user_filter)

            user = User()

            id, username, email, _, bio, join_date = row[0]

            user.id = id
            user.username = username
            user.email = email
            user.bio = bio
            user.join_date = join_date

            return user

        rows = read_rows('profile')
        users = []
        for r in rows:
            user = User()
            id, username, email, _, bio, join_date = r

            user.id = id
            user.username = username
            user.email = email
            user.bio = bio
            user.join_date = join_date

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


    def insert_user_table(self):
        insert_query = """
                INSERT INTO profile (id, username, email, password, bio, created_at, is_deleted)
                VALUES (DEFAULT, %s, %s, %s, %s, %s, %s);
                """

        params = [
            self.username,
            self.email,
            self.password,
            self.bio,
            self.join_date,
            self.is_deleted
        ]

        db_interface.run_query(insert_query, params)


    def update_user_table(self, soft_delete_flag=False):
        if soft_delete_flag:
            update_query = f"""
                        UPDATE profile
                        SET is_deleted = %s
                        WHERE id = %s;
                        """

            params = [
                self.is_deleted,
                self.id
            ]

            db_interface.run_query(update_query, params)

        else:
            update_query = f"""
                        UPDATE profile
                        SET username = %s, email = %s, password = %s, bio = %s, created_at = %s, is_deleted = %s
                        WHERE id = %s;
                        """

            params = [
                self.username,
                self.email,
                self.password,
                self.bio,
                self.join_date,
                self.is_deleted,
                self.id
            ]

            db_interface.run_query(update_query, params)

    def soft_delete(self):
        self.update_user_table(soft_delete_flag=True)


class Post(DBModel, UserMixin):
    db_columns = [
        ("id", "serial", "PRIMARY KEY"),
        ("title", "varchar(255)", "UNIQUE NOT NULL"),
        ("content", "text", "NOT NULL"),
        ("created_at", "timestamp", "DEFAULT current_timestamp NOT NULL"),
        ("view_count", "bigint", "NOT NULL"),
        ("author_id", "varchar(255)", "UNIQUE NOT NULL"),
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

    def read_user_rows(self, cond=None):
        if cond:
            query = "SELECT * FROM profile WHERE {} = %s AND is_deleted = False"
            params = [cond[1]]
            field_param = cond[0]
            rows = db_interface.run_query(query, params, field_param)
            return rows

        query = "SELECT * FROM profile WHERE is_deleted = False"
        rows = db_interface.run_query(query)
        return rows

    def query_users(self, user_filter=None):
        if user_filter:
            row = self.read_user_rows(user_filter)

            user = User()

            id, username, email, _, bio, join_date = row[0]

            user.id = id
            user.username = username
            user.email = email
            user.bio = bio
            user.join_date = join_date

            return user

        rows = self.read_user_rows()
        users = []
        for r in rows:
            user = User()
            id, username, email, _, bio, join_date = r

            user.id = id
            user.username = username
            user.email = email
            user.bio = bio
            user.join_date = join_date

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

    def insert_user_table(self):
        insert_query = """
                INSERT INTO profile (id, username, email, password, bio, created_at, is_deleted)
                VALUES (DEFAULT, %s, %s, %s, %s, %s, %s);
                """

        params = [
            self.username,
            self.email,
            self.password,
            self.bio,
            self.join_date,
            self.is_deleted
        ]

        db_interface.run_query(insert_query, params)

    def update_user_table(self, soft_delete_flag=False):
        if soft_delete_flag:
            update_query = f"""
                        UPDATE profile
                        SET is_deleted = %s
                        WHERE id = %s;
                        """

            params = [
                self.is_deleted,
                self.id
            ]

            db_interface.run_query(update_query, params)

        else:
            update_query = f"""
                        UPDATE profile
                        SET username = %s, email = %s, password = %s, bio = %s, created_at = %s, is_deleted = %s
                        WHERE id = %s;
                        """

            params = [
                self.username,
                self.email,
                self.password,
                self.bio,
                self.join_date,
                self.is_deleted,
                self.id
            ]

            db_interface.run_query(update_query, params)

    def soft_delete(self):
        self.update_user_table(soft_delete_flag=True)