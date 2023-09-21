from flask import Flask
from flask_bcrypt import Bcrypt
app = Flask(__name__)

from umbrella import routes