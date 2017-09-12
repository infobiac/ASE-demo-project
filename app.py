from flask import Flask, render_template, g, request, make_response, redirect, session
import requests
from sqlalchemy import *
from sqlalchemy.exc import IntegrityError
from collections import defaultdict

app = Flask(__name__)

DATABASEURI = "sqlite:///t1.db"

engine = create_engine(DATABASEURI)

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print("there was a connection error.")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/')
def hello_world():
    return render_template('home.html')


@app.route('/usr/login/', methods=['POST'])
def loginUser():
	email=request.form['email']
	c=g.conn.execute("SELECT email FROM users WHERE email=?", email)
	y = None
	for x in c:
		print(x)
		y=x[0]
	if y is not None:
		session['username']=email
		return redirect('/usr/home/')
	else:
		return "You don't have an account here yet. Go <a href=../..>home?</a>"

@app.route('/usr/signup/', methods=['POST'])
def signupUser():
	email=request.form['email']
	try:
		g.conn.execute('INSERT INTO users (email) VALUES (?)', email)
		session['username']=email
		return redirect('/usr/home/')
	except IntegrityError:
		return "You've registered before"

@app.route('/usr/home/')
def userHome():
	try:
		addresses = g.conn.execute("""SELECT b.burn_pattern
			FROM burners b, users u
			WHERE u.email=? AND b.email=u.email""", session['username'])
		a=[]
		for x in addresses:
			d=defaultdict(str)
			d["address"]=x["burn_pattern"]
			a.append(d)
		c=g.conn.execute("""SELECT u.email, b.burn_pattern, e.efrom, e.subj, e.body, e.eid
			FROM users u, burners b, emails e
			WHERE u.email=? AND u.email=b.email AND b.burn_pattern = e.burn_pattern
			""", session['username'])
		l=[]
		for x in c:
			d = defaultdict(str)
			d['email']=x['email']
			d['burn_pattern']=x['burn_pattern']
			d['efrom']=x['efrom']
			d['subj']=x['subj']
			d['body']=x['body']
			d['eid']=x['eid']
			l.append(d)
		return render_template("userhome.html", emails=l, addresses=a)
	except KeyError:
		return "not logged in"

@app.route('/logout/')
def logout():
	session.pop('username', None)
	return redirect('/')

@app.route('/burner/new/', methods=['POST'])
def newburn():
	pattern=request.form['username']
	fullpattern="{}@mg.christopherimann.com".format(pattern)
	user=session['username']
	try:
		g.conn.execute('INSERT INTO burners VALUES (?,?)', fullpattern, user)
		return "Burner created. Go <a href='/usr/home'>home?</a>"
	except IntegrityError:
		return "That username is taken. Please try another one <a href='/usr/home'>here</a>"


@app.route('/burner/processemail/', methods=['POST'])
def processmail():
	email=request.form
	eto = email.get('recipient')
	efrom = email.get('from')
	esubj = email.get('subject')
	body = email.get('body-html')
	g.conn.execute('INSERT INTO emails(burn_pattern, efrom, subj, body) VALUES(?, ?, ?, ?)', eto, efrom, esubj, body)
	return "We're good"

@app.route('/view/email/<mailid>')
def viewemail(mailid):
	c=g.conn.execute("""SELECT u.email, b.burn_pattern, e.efrom, e.subj, e.body
		FROM users u, burners b, emails e
		WHERE u.email=? AND u.email=b.email AND b.burn_pattern = e.burn_pattern AND e.eid=?
		""", session['username'], mailid)
	d = defaultdict(str)
	for x in c:
		d['email']=x['email']
		d['burn_pattern']=x['burn_pattern']
		d['efrom']=x['efrom']
		d['subj']=x['subj']
		d['body']=x['body']
	return render_template('mail.html', d=d, eid=mailid)

@app.route('/view/address/<addid>')
def viewaddress(addid):
	c=g.conn.execute("""SELECT u.email, b.burn_pattern, e.efrom, e.subj, e.body, e.eid
			FROM users u, burners b, emails e
			WHERE u.email=? AND u.email=b.email AND b.burn_pattern = e.burn_pattern AND b.burn_pattern=?
			""", session['username'], addid)
	l=[]
	for x in c:
			d = defaultdict(str)
			d['email']=x['email']
			d['burn_pattern']=x['burn_pattern']
			d['efrom']=x['efrom']
			d['subj']=x['subj']
			d['body']=x['body']
			d['eid']=x['eid']
			l.append(d)
	print(l)
	return render_template("address.html", ad=addid, emails=l)

@app.route('/delete/address/<addid>')
def deleteaddress(addid):
	c=g.conn.execute("""DELETE FROM burners
		WHERE burn_pattern=? AND email=?""", addid, session['username']
		)
	return redirect('/usr/home')

@app.route('/delete/email/<mailid>')
def deleteemail(mailid):
	c=g.conn.execute("""DELETE FROM emails
		WHERE eid=?""", mailid
		)
	return redirect('/usr/home')