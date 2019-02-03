from flask import Flask, request, session
from inner_functions import check_location, checkgeo_location, checkcustom_location
from tokens import client
import json
from default_classes import defaultCustomLocations

def setLocation(body, to_num, from_num):
    params = body.lower().split(' ')
    if len(params) > 1:
        client.messages.create(to=to_num, from_=from_num,body='Oops! Try again')
        session['state'] = 'error'
    elif len (params) == 1:
        client.messages.create(to=to_num, from_=from_num,body='What is the name of the location?')
        session['state'] = 'setCustomLocationName'
    return ''

def setCustomLocationName(body, to_num, from_num):
    params = body.lower().split(' ')
    if len(params) > 1:
        client.messages.create(to=to_num, from_=from_num,body='Oops! Location names must only be 1 word.')
        session['state'] = 'error'
    else:
        session['state'] = 'setCustomLocationLocation'
        session['locationVarName'] = body.lower()
        client.messages.create(to=to_num, from_=from_num,body='What is location of "' + body.lower() + '"?')
    return ''

def setCustomLocationLocation(body, to_num, from_num):
    var = session.get('locationVarName', '')
    loc = check_location(body)

    if var != '' and loc != '':
        session['locationVarLocation'] = loc
        session['state'] = 'confirmCustomLocation'
        client.messages.create(to=to_num, from_=from_num,body="Please confirm this is your location: " + loc)
    else:
        session['locationVarName'] = ''
        session['locationVarLocation'] = ''
        session['state'] = 'error'
        client.messages.create(to=to_num, from_=from_num,body='Error creating custom location. Please try again.')
    return ''

def confirmCustomLocation(body, to_num, from_num):
    var = session.get('locationVarName', '')
    loc = session.get('locationVarLocation', '')
    if var != '' and loc != '' and checkConfirm(body):
        exists = False
        customLoc = {'name': var, 'location': loc}
        customLocations = json.loads(session.get('customLocations', defaultCustomLocations))
        print(json.dumps(customLocations))
        newCustomLocations = json.loads(defaultCustomLocations)
        for custLoc in (customLocations['locations']):
            if custLoc['name'] == var:
                newCustomLocations['locations'].append(customLoc)
                exists = True
            else:
                newCustomLocations['locations'].append(loc)
        if exists == False:
            newCustomLocations['locations'].append(customLoc)
        session['customLocations'] = json.dumps(newCustomLocations)
        client.messages.create(to=to_num, from_=from_num,body='Set custom location "' + var + '" with value of "' + loc + '".')
        session['locationVarName'] = ''
        session['locationVarLocation'] = ''
        session['state'] = 'continue'
    else: 
        client.messages.create(to=to_num, from_=from_num,body='Okay, What is location of "' + var + '"?')
        session['state'] = 'setCustomLocationLocation'
        session['locationVarLocation'] = ''
    return ''

def getLocations(body, to_num, from_num):
    locs = session.get('customLocations', defaultCustomLocations)
    if locs == defaultCustomLocations:
        client.messages.create(to=to_num, from_=from_num,body="You don't have any stored locations.")
        return ''
    elif locs == '':
        session['customLocations'] = defaultCustomLocations
        client.messages.create(to=to_num, from_=from_num,body="Error. Pleaser Try Again")
        return ''
    else:
        message = "Your stored locations are:\n"
        print(locs)
        customLocations = json.loads(locs)
        for location in customLocations['locations']:
            print("asdfghjkljhgfdsfghjkljhgf" + json.dumps(location))
            message += 'kk'#ocation['name'] + ': ' + location['location'] + '\n'
        client.messages.create(to=to_num, from_=from_num,body=message)
    return ''

def removeLocations(body, to_num, from_num):
    locs = session.get('customLocations', defaultCustomLocations)
    if locs == defaultCustomLocations:
        client.messages.create(to=to_num, from_=from_num,body="You don't have any stored locations.")
    else:
        session['customLocations'] = defaultCustomLocations
        client.messages.create(to=to_num, from_=from_num,body="Successfully removed stored locations.")
    return ''

def getTo(body, to_num, from_num):
    toLoc = checkcustom_location(body)

    if toLoc != "":
        session['to_location'] = toLoc
        session['state'] = 'confirmTo'
        confirmto = "Please confirm this is your destination: " + toLoc
        client.messages.create(to=to_num, from_=from_num,body=confirmto)
        return toLoc
    else:
        client.messages.create(to=to_num, from_=from_num, body="Sorry, please check that your location exists on planet earth.")
        setGetTo(body, to_num, from_num)
    return ''

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
    return ''

def getFrom(body, to_num, from_num):
    fromLoc = checkcustom_location(body)

    if fromLoc != "":
        session['from_location'] = fromLoc
        session['state'] = 'confirmFrom'
        confirmfrom = "Please confirm this is where you are coming from: " + fromLoc
        client.messages.create(to=to_num, from_=from_num,body=confirmfrom)
        return fromLoc
    else:
        client.messages.create(to=to_num, from_=from_num,
                               body="Sorry, please check that your location exists on planet earth.")
        setGetFrom(body, to_num, from_num)
    return ''

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
    return ''

def getHelp(body, to_num, from_num):
    helpMsg = 'Tell TextHome where you want to go and additional prompts will help you through the process.\n\n'
    helpMsg += 'If you don\'t know your current location you can ask "Where Am I" to TextHome\n\n'
    helpMsg += 'Additional Functions:\n'
    helpMsg += 'clear: This will clear your locations\n'
    helpMsg += 'clear-all: This will clear all your saved data\n'
    helpMsg += 'set-location: This will walk you through the process of creating a custom saved location\n'
    helpMsg += 'get-locations: This will show all your saved locations\n'
    helpMsg += 'remove-locations: This will remove your saved locations'
    client.messages.create(to=to_num, from_=from_num,body=helpMsg)
    return''

def sendThanks(body, to_num, from_num):
    client.messages.create(to=to_num, from_=from_num,body="You're Welcome! 😊")
    return''

def sendLocationHelp(body, to_num, from_num):
    client.messages.create(to=to_num, from_=from_num,media_url="https://i.imgur.com/nj0RiEe.jpg", body="Other Text")
    return''

def checkConfirm(message):
    txt = message.lower()
    if (txt == 'yes' or txt == 'y' or txt == 'ye' or txt == 'yea' or txt == 'oui' or txt == 'yup' or txt == 'yep'):
        return True
    else:
        return False

def clearConversationState():
    session['state'] = ''
    session['to_location'] = ''
    session['from_location'] = ''
    session['transport_mode'] = ''
    session['confirmed_to'] = 0
    session['confirmed_from'] = 0
    return ''