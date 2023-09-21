from flask import Flask
from flask_bcrypt import Bcrypt
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('UMBRELLA_SECRET_KEY')
bcrypt = Bcrypt(app)

from umbrella import routes