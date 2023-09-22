from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from  flask_ckeditor import CKEditor
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('UMBRELLA_SECRET_KEY')

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
ckeditor = CKEditor(app)

from umbrella import routes