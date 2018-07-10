# Project 1

Web Programming with Python and JavaScript

Login/Register Features:
Login catches incomplete form submission and returns you to an error page
Register button will auto-fill username if username was filled out in login form
Registration will auto login with newly created username
Register catches incomplete form submission and returns back to register page with previously filled in username
Register has a log in button as well

Search features:
Results will first try to match zipcode (zipcode is treated as an integer, so no wildcards)
    If zipcode is found, return the unique result
    If zipcode is not found, try city and state (form can handle incomplete information ie. only state or only city)
Results are ordered by zipcode
Hovering over a result changes its color
Can navigate between different pages of search results
Page remembers previous search query
    ***Page will not query database if search query has not changed***
    ***Page will remember what page of the results you were on if query has not changed***

Places features:
Can only be accessed by logged in users
Places remembers previous found place
    ***Places will not query database if the selected place has not changed***
    ***Places will generate the previous found place if accessed outside of clicking a search result***
Places will display alert if no comments found
Like the search, comments can be searched through using next and prev (position is saved if place is not changed)
Comments sorted by descending order of time posted (newest coments are at the start, oldest are at the end)
Option to post removed if user already posted