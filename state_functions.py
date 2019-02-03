from flask import Flask, request, session
from inner_functions import check_location, checkgeo_location
from tokens import client
import json


defaultLocations = json.dumps({'locations':[]})

def setLocation(body, to_num, from_num):
    clearConversationState()
    params = body.lower().split(' ')
    if len(params) > 2:
        client.messages.create(to=to_num, from_=from_num,body='Oops! Locations must only be 1 word.')
    elif len (params) == 1:
        client.messages.create(to=to_num, from_=from_num,body='What is the name of the location?')
        session['state'] = 'setCustomLocationName'
    else:
        var = params[1]
        client.messages.create(to=to_num, from_=from_num,body='What is location of "' + var + '"?')
        session['state'] = 'setCustomLocation'
        session['locationVarName'] = var

def getLocations(body, to_num, from_num):
    locs = session.get('customLocations', defaultLocations)
    if locs == defaultLocations:
        client.messages.create(to=to_num, from_=from_num,body="You don't have any stored locations.")
    else:
        message = "Your stored locations are:\n"
        customLocations = json.loads(locs)
        for location in customLocations['locations']:
            message += location['name'] + ': ' + location['location'] + '\n'
        client.messages.create(to=to_num, from_=from_num,body=message)

def removeLocations(body, to_num, from_num):
    locs = session.get('customLocations', defaultLocations)
    if locs == defaultLocations:
        client.messages.create(to=to_num, from_=from_num,body="You don't have any stored locations.")
    else:
        session['customLocations'] = defaultLocations
        client.messages.create(to=to_num, from_=from_num,body="Successfully removed stored locations.")

def getTo(body, to_num, from_num):
    toLoc = check_location(body)

    if toLoc != "":
        session['to_location'] = toLoc
        session['state'] = 'confirmTo'
        confirmto = "Please confirm this is your destination: " + toLoc
        client.messages.create(to=to_num, from_=from_num,body=confirmto)
        return toLoc
    else:
        setGetTo(body, to_num, from_num)

def confirmTo(body, to_num, from_num):
    if (checkConfirm(body)):
        session['confirmed_to'] = 1
        return True
    else:
        setGetTo(body, to_num, from_num)
        return False

def setGetTo(body, to_num, from_num):
    session['state'] = 'getTo'
    client.messages.create(to=to_num, from_=from_num,body="Okay, where do you want to go?")




def getFrom(body, to_num, from_num):
    fromLoc = checkgeo_location(body)

    if fromLoc != "":
        session['from_location'] = fromLoc
        session['state'] = 'confirmFrom'
        confirmfrom = "Please confirm this is where you are coming from: " + fromLoc
        client.messages.create(to=to_num, from_=from_num,body=confirmfrom)
        return fromLoc
    else:
        setGetFrom(body, to_num, from_num)

def confirmFrom(body, to_num, from_num):
    if (checkConfirm(body)):
        session['confirmed_from'] = 1
        return True
    else:
        setGetFrom(body, to_num, from_num)
        return False

def setGetFrom(body, to_num, from_num):
    session['state'] = 'getFrom'
    client.messages.create(to=to_num, from_=from_num,body="Okay, where are you?")

def getHelp(body, to_num, from_num):
    client.messages.create(to=to_num, from_=from_num,body="Okay, where are you?")
    return''

def checkConfirm(message):
    txt = message.lower()
    if (txt == 'yes' or txt == 'y' or txt == 'ye' or txt == 'yea' or txt == 'oui' or txt == 'yup' or txt == 'yep'):
        return True
    else:
        return False

def clearConversationState():
    session['state'] = 'new'
    session['to_location'] = ''
    session['from_location'] = ''
    session['transport_mode'] = ''
    session['confirmed_to'] = 0
    session['confirmed_from'] = 0