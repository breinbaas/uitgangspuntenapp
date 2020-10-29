from flask import render_template, url_for, redirect, request
from app import app
from app.forms import DTForm
from app.dbconnector import get_uitgangspunten


@app.route('/', methods=['GET', 'POST'])
def index():
    form = DTForm()    
    dtcode = request.form.get("dtcode")
    try:
        dtchainage = int(request.form.get("dtchainage"))
    except:
        dtchainage = 0

    if dtcode: 
        dtinfo = get_uitgangspunten(dtcode, dtchainage)  
        return render_template('index.html', form=form, dtinfo=dtinfo)
    else:
        return render_template('index.html', form=form)
