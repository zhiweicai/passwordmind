from flask import Flask, render_template, session, redirect, url_for,flash
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField,SubmitField,TextAreaField
from wtforms.validators import Required,Optional
from flask.ext.sqlalchemy import SQLAlchemy
import os.path
from flask.ext.login import login_user,logout_user, login_required,LoginManager,UserMixin
from flask.ext.script import Manager,Shell
from flask.ext.migrate import Migrate, MigrateCommand





basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

bootstrap = Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] =\
'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'

manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)



class PasswordForm(Form):
    website = StringField('Site', validators=[Required()])
    username = StringField('Username', validators=[Required()])
    password = StringField('Password', validators=[Required()])
    details = TextAreaField('Detail', validators=[Optional()])
    submit = SubmitField('Submit')


class LoginForm(Form):
    username = StringField('Username', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Log In')


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is not None and user.password == form.password.data :
            login_user(user,True)
            return render_template('index.html')
        flash ('Invalid username or password!')
    return render_template('login.html', form=form)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/View')
@login_required
def view():
    allrecords = PasswordRecords.query.all ()
    return render_template('records.html',recordcount=len(allrecords),records=allrecords)


@app.route('/item/<id>')
@login_required
def item(id):
    myitem = PasswordRecords.query.get_or_404(id)
    site = myitem.displayname
    username = myitem.username
    password = myitem.password
    detail = myitem.detail
    return render_template('item.html',name=site,name2="http://" + site,username=username,password=password,detail=detail)


@app.route('/deleteitem/<id>')
@login_required
def deleteitem(id):
    myitem = PasswordRecords.query.get_or_404(id)
    db.session.delete (myitem)
    db.session.commit ()
    flash('record has been deleted!')
    return render_template('index.html')


@app.route('/edititem/<id>', methods=['GET', 'POST'])
@login_required
def edititem(id):
    myitem = PasswordRecords.query.get_or_404(id)

    form = PasswordForm()
    if form.validate_on_submit():
            myitem.displayname = form.website.data
            myitem.username = form.username.data
            myitem.password = form.password.data
            myitem.detail = form.details.data
            db.session.add (myitem)
            db.session.commit ()
            return render_template('UpdateSuccess.html',recordname = myitem.displayname)

    form.website.data = myitem.displayname
    form.username.data = myitem.username
    form.password.data = myitem.password
    form.details.data = myitem.detail

    return render_template('edititem.html',name="adding",form = form)


@app.route('/Add', methods=['GET', 'POST'])
@login_required
def add ():
    name = None
    form = PasswordForm()
    if form.validate_on_submit():
        sName = form.website.data
        sUser = form.username.data
        sPassword = form.password.data
        sDetail = form.details.data

        session['recordname'] = sName
        newsite = PasswordRecords.query.filter_by(displayname=sName).first()
        if newsite is None:
           newsite = PasswordRecords (displayname=sName,username=sUser, password=sPassword,detail = sDetail)
           db.session.add (newsite)
           form.website.data = ''
           db.session.commit ()
           return render_template('AddSuccess.html',recordname = session.get('recordname'))
        return render_template('Duplicate.html',recordname = session.get('recordname'))
    return render_template('AddRecord.html', form=form)



class Users(UserMixin,db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=False)
    password = db.Column(db.String(80), unique=False)

    def __init__(self, username,password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username


class PasswordRecords(db.Model):
    __tablename__ = 'passwordrecord'
    id = db.Column(db.Integer, primary_key=True)
    displayname = db.Column(db.String(80), unique=False)
    username = db.Column(db.String(80), unique=False)
    password = db.Column(db.String(80), unique=False)
    detail = db.Column(db.String(512), unique=False)

    def __init__(self, displayname, username,password,detail):
        self.displayname = displayname
        self.username = username
        self.password = password
        self.detail = detail

    def __repr__(self):
        return '<Record %r>' % self.displayname

def make_shell_context():
    return dict(app=app, db=db, Users=Users, PasswordRecords=PasswordRecords)
manager.add_command("shell", Shell(make_context=make_shell_context))


if __name__ == '__main__':
    manager.run()
