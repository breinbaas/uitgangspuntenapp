from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField, validators
from app.dbconnector import get_all_codes

class DTForm(FlaskForm):
    dtcodes = get_all_codes()
    choices = [(c,c) for c in dtcodes]
    dtcode = SelectField('Dijktraject code', choices=choices)
    dtchainage = IntegerField('Metrering', default=0, validators=[
                validators.Required(),
                validators.NumberRange(min=0, max=10000)                
            ])
    submit = SubmitField('Submit')
