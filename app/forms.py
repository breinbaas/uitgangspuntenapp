from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from app.dbconnector import get_all_codes

class DTForm(FlaskForm):
    dtcodes = get_all_codes()
    choices = [(c,c) for c in dtcodes]
    dtcode = SelectField('Dijktraject code', choices=choices)
    submit = SubmitField('Submit')
