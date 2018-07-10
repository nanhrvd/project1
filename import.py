import os
import csv

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


f = open("zips.csv")
reader = csv.reader(f)
for Zipcode, City, State, Lat, Long, Population in reader:
    db.execute("INSERT INTO places (zipcode, city, state, lat, long, population) VALUES (:zip, :city, :state, :lat, :longi, :population)",
                {'zip':Zipcode, 'city':City, 'state':State, 'lat':Lat, 'longi':Long, 'population':Population})
    print(f"Added place zip {Zipcode}, city {City}, state {State}.")
db.commit()