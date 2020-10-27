import os

from flask import Flask, request, render_template, redirect, url_for
from config import Config

project_root = os.path.dirname(os.path.realpath('__file__'))
template_path = os.path.join(project_root, 'app/templates')
static_path = os.path.join(project_root, 'app/static')
app = Flask(__name__, template_folder=template_path, static_folder=static_path)
app.config.from_object(Config)

from app import routes