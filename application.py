import os
import hashlib

from flask import Flask, session, render_template, request, url_for, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    # initialize global varaiables
    if 'user_id' not in session:
        session['user_id'] = 0
    if 'results' not in session:
        session['results'] = ['']
    if 'index' not in session:
        session['index'] = 0
    if 'query' not in session:
        session['query'] = ('', '', '')
    # stri = "no sql"

    # get input data
    city = request.args.get('city', '')
    state = request.args.get('state', '')
    zipreal = request.args.get('zipcode', -1)
    if zipreal == '':
        zipcode = int(-1)
    else:
        zipcode = int(zipreal)

    # if no input, use last recorded query
    if (city, state, zipcode) == ('', '', -1):
        old_query = session['query']
        city = old_query[0]
        state = old_query[1]
        if old_query[2] != '':
            zipcode = old_query[2]

    # if current query is different from last query and not empty
    # update query and get new results
    elif (city, state, zipreal) != session['query']:
        session['query'] = (city, state, zipreal)
        sql0 = "SELECT city, state, zipcode, population, lat, long FROM places "
        # query the zipcode (can't wildcard zipcode b.c it is an integer primary key)
        if int(zipcode) != -1:
            # stri = sql0 + "WHERE zipcode= %d" % (int(zipcode))
            temp = db.execute(sql0 + "WHERE zipcode= %d" % (int(zipcode))).fetchone()
            subset = [temp]

            if temp is not None:
                # found location, return to mainpage
                session['results'] = subset
                return render_template('index.html',
                            user_id=session['user_id'],
                            city=city,
                            state=state,
                            zipcode=zipreal,
                            # stri=stri,
                            results=subset);
        # if zipcode fails, try %city% and state, sort by zipcode
        if city == '' and state == '' :
            sql1 = ''
        elif city == '':
            sql1 = "WHERE lower(state) LIKE lower(:state)"
        elif state == '':
            sql1 = "WHERE lower(city) LIKE lower(:like_city)"
        else:
            sql1 = "WHERE lower(city) LIKE lower(:like_city) AND state=:state"
        like_city = "%" + city + "%"
        sql2 = "SELECT * FROM ("
        sql3 = ") temp ORDER BY temp.zipcode"
        arg = {'like_city':like_city, 'state':state}
        temp = db.execute(sql2+sql0+sql1+sql3, arg).fetchall()
        # stri=sql2+sql0+sql1+sql3, arg
        session['results'] = temp

    # get and parse results (should not be None)
    results = session['results']
    if results == None:
        return redirect(url_for('error',
                                ret='index',
                                return_message="Go back to the main page!"))
    elif (results == ['']) or (results == []):
        subset = results
    else:
        index = session['index']
        results[index*10 : (index+1)*10]
        subset = results

    return render_template('index.html',
                            user_id=session['user_id'],
                            city=city,
                            state=state,
                            zipcode=zipreal,
                            # stri=stri,
                            results=subset);

@app.route("/logout", methods=["POST","GET"])
def logout():
    session['user_id'] = 0
    return redirect(url_for('index'));

@app.route("/error")
def error():
    # intialize user id
    if(not 'user_id' in session):
        session['user_id'] = 0;

    # get error message from parameters
    error = request.args.get('error', None)
    return_message = request.args.get('return_message', None)
    arg_ret = request.args.get('ret', None)
    try:
        ret = url_for(arg_ret)
    except:
        ret = None

    return render_template("error.html",
        error=error,
        ret=ret,
        return_message=return_message,
        user_id=session['user_id'])

@app.route("/login", methods=["POST", "GET"])
def login():
    # allowing get ensures site doesn't fail if /login called directly
    if request.method == "GET":
        return redirect(url_for('index'))

    # get data from form, ensure all fields filled
    username_form  = request.form['username']
    password_form  = request.form['password']
    if username_form == '' or password_form == '':
        return redirect(url_for('error',
            error="Please enter both username and password!",
            ret='index',
            return_message="Go back to the main page!"))

    # search for user, then check hashed pw
    row = db.execute("SELECT DISTINCT user_id, password FROM users WHERE lower(username) = lower(:username)",
                    {"username": username_form}).fetchone()
    if row is not None:
        m = hashlib.md5()
        m.update(password_form.encode('utf-8'))
        pw_hash = m.hexdigest()
        if(pw_hash == row[1]):
            session['user_id'] = row[0]
            return redirect(url_for('index'))

    # error case
    return redirect(url_for('error',
        error="Invalid login. Username or Password incorrect.",
        ret=url_for('index'),
        return_message="Go back to the main page!"))

@app.route("/register", methods=["POST", "GET"])
def register():
    # check if user already logged in
    if 'user_id' in session and session['user_id'] != 0:
        return redirect(url_for('index'))

    # check if there is prior insert of username
    if request.method == "POST":
        username_form = request.form['username']
    else:
        username_form = request.args.get('default_username', '')

    # check for error message
    error = request.args.get('error', None)

    return render_template("register.html",
        default_username=username_form,
        error=error);

@app.route("/registration", methods=["POST", "GET"])
def registration():
    # see above note on why note methods=["POST"]
    if request.method != "POST":
        return redirect(url_for('register'))

    # check if already logged in
    if 'user_id' in session and session['user_id'] != 0:
        return redirect(url_for('index'))

    # check fields filled
    username_form = request.form['username']
    password_form = request.form['password']
    if username_form == '' or password_form == '':
        return redirect(url_for('register',
            default_username=username_form,
            error="Please enter both username and password!"))

    # check username available
    row = db.execute("SELECT DISTINCT user_id FROM users WHERE lower(username) = lower(:username)",
                    {"username": username_form}).fetchone()
    if row is not None:
        return redirect(url_for('register',
            default_username=username_form,
            error="Please use a different username!"))

    # insert username and hashed pw, commit for atomicity
    m = hashlib.md5();
    m.update(password_form.encode('utf-8'))
    pw_hash = m.hexdigest()
    db.execute("INSERT INTO users (username, password) VALUES (:user, :pw)",
                {"user": username_form, "pw": pw_hash})
    db.commit()

    # log the user in
    uid = db.execute("SELECT DISTINCT user_id FROM users WHERE lower(username) = lower(:user)",
                    {"user": username_form}).fetchone()
    session['user_id'] = uid[0]
    return redirect(url_for('index'))