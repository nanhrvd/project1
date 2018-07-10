import os
import hashlib
import requests, json
from datetime import datetime
from dateutil import tz
import pytz
import json

from flask import Flask, session, render_template, request, url_for, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# API key
# TODO: how to hide api key
DS_KEY = "68e6092785397a30a1e9c98c64ad242d"

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

# Sets how many results to display
display = 5

@app.route("/")
def index():
    # initialize global varaiables
    if 'user_id' not in session:
        session['user_id'] = 0
    if 'results' not in session:
        session['results'] = ['']
    if 'indices' not in session:
        session['indices'] = {"search_index":int(0), "places_index":int(0)}
    if 'query' not in session:
        session['query'] = ('', '', '')

    # get input data
    city = request.args.get('city', '')
    state = request.args.get('state', '')
    zipreal = request.args.get('zipcode', '')
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
        session['indices']['search_index'] = 0
        sql0 = "SELECT city, state, zipcode, population, lat, long FROM places "
        # query the zipcode (can't wildcard zipcode b.c it is an integer primary key)
        if int(zipcode) != -1:
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
        session['results'] = temp

    # get and parse results (should not be None)
    # [''] means it is user's first time on page
    # [] means no results found
    results = session['results']
    if results == None:
        return redirect(url_for('error',
                                ret='index',
                                return_message="Go back to the main page!"))
    elif (results == ['']) or (results == []):
        subset = results
    else:
        index = session['indices']['search_index']
        subset = results[index*display : (index+1)*display]

    query = session['query']
    return render_template('index.html',
                            user_id=session['user_id'],
                            city=query[0],
                            state=query[1],
                            zipcode=query[2],
                            results=subset);

@app.route("/places")
def places():
    if 'zip' not in session:
        session['zip'] = 0
    if 'comments' not in session:
        session['comments'] = []
    if 'place' not in session:
        session['place'] = None
    if 'posted' not in session:
        session['posted'] = False;
    if 'user_id' not in session:
        session['user_id'] = 0
    if 'weather' not in session:
        session['weather'] = {}

    # check logged in
    user_id = session['user_id']
    if user_id == 0:
        error = "Only users can view and post comments!"
        message = "Please return to main page and log in!"
        return redirect(url_for('error', error=error, ret='index', return_message=message))

    # get inputted or last selected zipcode, return to index if no zipcode
    zipcode = request.args.get('zipcode', 0)
    if zipcode == 0:
        zipcode = session['zip']

    if zipcode == 0:
        return redirect(url_for('index'))

    # return cached results if zip is same as before
    if zipcode == session['zip']:
        comments = session['comments']
        index = session['indices']['places_index']
        subset = comments[index*display : (index+1)*display]
        return render_template("places.html",
                                user_id=user_id,
                                place=session['place'],
                                weather=session['weather'],
                                comments=subset,
                                posted=session['posted'])

    # get sql data on zipcode, update last selected zipcode
    sql0 = "SELECT city, state, zipcode, population, lat, long FROM places WHERE zipcode= %d"
    place = db.execute(sql0 % (int(zipcode))).fetchone()

    # if zipcode is invalid, return error back to index
    if place is None:
        error = "No location found with the zipcode you inputted!"
        message = 'Please go back to homepage!'
        return redirect(url_for('error', error=error, ret='index', return_message=message))

    # format city to capitalize
    placedata = list(place)
    placedata[0] = placedata[0].lower().capitalize()
    session['zip'] = int(zipcode)
    session['place'] = placedata

    # get weather
    weather_request = "https://api.darksky.net/forecast/%s/%s,%s"
    weather = requests.get(weather_request % (DS_KEY, place[4], place[5])).json()
    # weather = weather.json()
    currently = weather['currently']
    summary = currently['summary']
    temp = currently['temperature']
    tempApp = currently['apparentTemperature']
    dewpoint = currently['dewPoint']
    humidity = int(float(currently['humidity'])*100)

    # parse time
    time_zone = tz.gettz(weather['timezone'])
    t_raw = datetime.fromtimestamp(currently['time']).strftime('%A %m %d %H:%M:%S %Y')
    t_parse = datetime.strptime(t_raw, '%A %m %d %H:%M:%S %Y')
    t_aware = pytz.utc.localize(t_parse)
    t_zone = t_aware.astimezone(time_zone)
    t_final = t_zone.strftime('%A %b %d %Y %H:%M:%S')

    # store weather
    parsed_weather = [t_final, summary, temp, tempApp, dewpoint, humidity]
    session['weather'] = parsed_weather

    # get comments
    sql1 = "SELECT * FROM (SELECT comment, id, user_id FROM comments WHERE zipcode=%d) temp ORDER BY temp.id DESC"
    comments = db.execute(sql1 % (int(zipcode))).fetchall()
    session['comments'] = comments

    # check if user already posted
    posted = False
    for comment in comments:
        if comment[2] == user_id:
            posted = True
            break
    session['posted'] = posted

    index = session['indices']['places_index']
    subset = comments[index*display : (index+1)*display]

    return render_template("places.html",
                            user_id=user_id,
                            place=placedata,
                            weather=parsed_weather,
                            comments=subset,
                            posted=posted)

@app.route("/comment", methods=["POST", "GET"])
def comment():
    if request.method == "GET" or session['posted'] == True:
        return render_template(url_for('places'))

    # invariant: at this point places, zipcode, and user_id must be not None in session
    zipcode = int(session['zip'])
    user_id = int(session['user_id'])
    # double check user hasn't posted
    sql0 = "SELECT * FROM comments WHERE zipcode=%d AND user_id=%d"
    check = db.execute(sql0 % (zipcode, user_id)).fetchone()
    if check is not None:
        session['posted'] = True
        return redirect(url_for('places'))

    comment = request.form['comment']
    sql1 = "INSERT INTO comments (zipcode, user_id, comment) VALUES (%d, %d, :comment)"
    db.execute(sql1 % (zipcode, user_id), {'comment':comment})
    db.commit()
    session['posted'] = True

    sql2 = "SELECT * FROM (SELECT comment, id, user_id FROM comments WHERE zipcode=%d) temp ORDER BY temp.id DESC"
    session['comments'] = db.execute(sql2 % (zipcode)).fetchall()
    return redirect(url_for('places'))



@app.route("/logout", methods=["POST","GET"])
def logout():
    session.clear()
    session['user_id'] = 0
    return redirect(url_for('index'));

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

# increments search index
@app.route("/inc")
def inc_si():
    s_delta = int(request.args.get('s_delta', 0))
    p_delta = int(request.args.get('p_delta', 0))
    if s_delta == 0 and p_delta == 0:
        return redirect(url_for('index'))
    if s_delta != 0 and p_delta != 0:
        return redirect(url_for('error', error='Please browse search options through the \"next\" and \"previous\" buttons!'))

    # initialize global varaiables
    if 'results' not in session:
        session['results'] = ['']
    if 'comments' not in session:
        session['comments'] = []
    if 'indices' not in session:
        session['indices'] = {"search_index":int(0), "places_index":int(0)}

    # increment search index
    if s_delta != 0:
        leng = len(session['results'])
        ind = session['indices']['search_index']
        max_leng = int(leng / display - (leng % display == 0))

        if ind + s_delta < 0:
            session['indices']['search_index'] = 0
        elif ind + s_delta > max_leng:
            session['indices']['search_index'] = max_leng
        else:
            session['indices']['search_index'] = ind+s_delta
        return redirect(url_for('index'))
    # increment places page comment index
    else:
        comm = session['comments']
        leng = len(session['comments'])
        ind = session['indices']['places_index']
        max_leng = int(leng / display - (leng % display == 0))

        if ind + p_delta < 0:
            session['indices']['places_index'] = 0
        elif ind + p_delta > max_leng:
            session['indices']['places_index'] = max_leng
        else:
            session['indices']['places_index'] = ind+p_delta
        return redirect(url_for('places'))

# catch bad api call
@app.route("/api")
@app.route("/api/")
def api():
    if 'zip' not in session or session['zip'] == 0:
        error = "Error 404 Not found: please query api by using /api/<zipcode>"
        message = 'Please go back to homepage!'
        return redirect(url_for('error', error=error, ret='index', return_message=message))
    else:
        return redirect("/api/%s" % (session['zip']))

# places api
from flask_restful import Resource, Api
from flask_jsonpify import jsonify
api = Api(app)

class PlaceData(Resource):
    def get(self, zipcode):
        # get location info
        sql0 = "SELECT city, state, lat, long, zipcode, population FROM places WHERE zipcode= %d"
        place = db.execute(sql0 % (int(zipcode))).fetchone()

        # if zipcode is invalid, return 404 not found back to index
        if place is None:
            error = "Error 404 Not found: no location found with the zipcode you inputted!"
            message = 'Please go back to homepage!'
            return redirect(url_for('error', error=error, ret='index', return_message=message))

        # get comment count
        sql1 = "SELECT * FROM (SELECT comment, id, user_id FROM comments WHERE zipcode=%d) temp ORDER BY temp.id DESC"
        counter = db.execute(sql1 % (int(zipcode))).rowcount

        zip_str = str(zipcode)
        if int(zipcode) <= (9999):
            zip_str = "0" + zip_str

        ret = {"place_name":place[0],
            "state":place[1],
            "latitude":place[2],
            "longitude":place[3],
            "zip":zip_str,
            "population":place[5],
            "check_ins":counter}
        return jsonify(ret)

api.add_resource(PlaceData, '/api/<zipcode>')
