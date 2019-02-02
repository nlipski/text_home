from flask import Flask, request, session
from default_messages import checkConfirm
from inner_functions import check_location
from tokens import client

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

def getTo(body, to_num, from_num):
    toLoc = check_location(body)
    session['to_location'] = toLoc
    session['state'] = 'confirmTo'
    confirmto = "Please confirm this is your destination: " + toLoc
    client.messages.create(to=to_num, from_=from_num,body=confirmto)
    return toLoc

def confirmTo(body, to_num, from_num):
    if (checkConfirm(body)):
        session['confirmed_to'] = 1
        return True
    else:
        session['state'] = 'getTo'
        wheretogo = "Okay, where do you want to go?"
        client.messages.create(to=to_num, from_=from_num,body=wheretogo)
        return False

def getFrom(body, to_num, from_num):
    fromLoc = check_location(body)
    session['from_location'] = fromLoc
    session['state'] = 'confirmFrom'
    confirmfrom = "Please confirm this is where you are coming from: " + fromLoc
    client.messages.create(to=to_num, from_=from_num,body=confirmfrom)
    return fromLoc

def confirmFrom(body, to_num, from_num):
    if (checkConfirm(body)):
        session['confirmed_from'] = 1
        return True
    else:
        session['state'] = 'getTo'
        wheretogo = "Okay, where do you want to go?"
        client.messages.create(to=to_num, from_=from_num,body=wheretogo)
        return False

def clearConversationState():
    session['state'] = 'new'
    session['to_location'] = ''
    session['from_location'] = ''
    session['transport_mode'] = ''
    session['confirmed_to'] = 0
    session['confirmed_from'] = 0