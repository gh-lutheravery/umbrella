from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from  flask_ckeditor import CKEditor
from flask_view_counter import ViewCounter
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('UMBRELLA_SECRET_KEY')

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
app.config['CKEDITOR_PKG_TYPE'] = 'basic'
ckeditor = CKEditor(app)

view_counter = ViewCounter(app)

from umbrella import routes