import os
import dotenv
from flask import Flask
from flask_migrate import Migrate

dotenv.load_dotenv()

app = Flask(__name__)

app.config.from_mapping(
    SECRET_KEY='dev',
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ECHO=True
)

import models
models.db.init_app(app)
migrate = Migrate(app, models.db)

import routes