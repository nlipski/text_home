from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, session
import googlemaps
from inner_functions import get_locations, check_location, google_api_key, parse_directions, locationsClass
from default_messages import getHelp, checkConfirm, storedLocationClass
import datetime
import json

SECRET_KEY = 'be3e360b8fd84f3855468d2a1511cc04'
app = Flask(__name__)
app.config.from_object(__name__)

gmaps = googlemaps.Client(key=google_api_key)

account = "ACd6f3f6f499dc943cbca7ee0ce16aff6e"
token = "8377bf56ca922921e9b61547d951c018"
client = Client(account, token)

defaultLocations = json.dumps({'locations':[]})


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    body = request.values.get('Body', None)
    to_num = request.values.get('From', None)
    from_num = request.values.get('To', None)

    if body.lower() == 'clear session' or body.lower() == 'clear' or body.lower() == 'reset':
        clearConversationState()
        client.messages.create(to=to_num, from_=from_num,body='Session cleared successfully!')
        return ''
    elif body.lower() == 'map-help':
        client.messages.create(to=to_num, from_=from_num,body=getHelp())
        return ''
    elif body.lower().startswith('set-location'):
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
        return ''
    elif body.lower() == 'get-locations':
        locs = session.get('customLocations', '')
        if locs == '' or locs == defaultLocations:
            client.messages.create(to=to_num, from_=from_num,body="You don't have any stored locations.")
        else:
            message = "Your stored locations are:\n"
            customLocations = json.loads(locs)
            for location in customLocations['locations']:
                message += location['name'] + ': ' + location['location'] + '\n'
            client.messages.create(to=to_num, from_=from_num,body=message)
        return ''
    elif body.lower() == 'remove-locations':
        locs = session.get('customLocations', '')
        if locs == '' or locs == defaultLocations:
            client.messages.create(to=to_num, from_=from_num,body="You don't have any stored locations.")
        else:
            session['customLocations'] = defaultLocations
            client.messages.create(to=to_num, from_=from_num,body="Successfully removed stored locations.")
        return ''
    else:
        state = session.get('state', 'new')
        lastTime = session.get('message_time', '')
        now = datetime.datetime.now()
        FMT = '%d-%m-%Y_%H:%M:%S'
        session['message_time'] = now.strftime(FMT)

        confirmedTo = session.get('confirmed_to', 0)
        confirmedFrom = session.get('confirmed_from', 0)

        locations = locationsClass()

        if lastTime == '':
            clearConversationState()
            locations.toLoc = ''
            locations.fromLoc = ''
            locations.mode = ''
            state = 'new'
        else:
            timeDiff = now - datetime.datetime.strptime(lastTime, FMT)
            if timeDiff < datetime.timedelta(minutes=5):
                locations.toLoc = session.get('to_location', '')
                locations.fromLoc = session.get('from_location', '')
                locations.mode = session.get('transport_mode', '')
            else:
                clearConversationState()
                locations.toLoc = ''
                locations.fromLoc = ''
                locations.mode = ''
                state = 'new'
                confirmedTo = 0
                confirmedFrom = 0

        checkLocations = 0
        if state == 'new':
            locations = get_locations(body)
            session['locations'] = locations.toLoc
            session['from_location'] = locations.fromLoc
            session['transport_mode'] = locations.mode
            checkLocations = 1
        elif state == 'getTo':
            locations.toLoc = check_location(body)
            session['to_location'] = locations.toLoc
            session['state'] = 'confirmTo'
            confirmto = "Please confirm this is your destination: " + locations.toLoc
            client.messages.create(to=to_num, from_=from_num,body=confirmto)
        elif state == 'getFrom':
            locations.fromLoc = check_location(body)
            session['from_location'] = locations.fromLoc
            session['state'] = 'confirmFrom'
            confirmfrom = "Please confirm this is where you are coming from: " + locations.fromLoc
            client.messages.create(to=to_num, from_=from_num,body=confirmfrom)
        elif state == 'confirmTo':
            if (checkConfirm(body)):
                confirmedTo = 1
                session['confirmed_to'] = confirmedTo
                checkLocations = 1
            else:
                session['state'] = 'getTo'
                wheretogo = "Okay, where do you want to go?"
                client.messages.create(to=to_num, from_=from_num,body=wheretogo)
        elif state == 'confirmFrom':
            if (checkConfirm(body)):
                confirmedFrom = 1
                session['confirmed_from'] = confirmedFrom
                checkLocations = 1
            else:
                session['state'] = 'getFrom'
                wheretogo = "Okay, where are you?"
                client.messages.create(to=to_num, from_=from_num,body=wheretogo)
        elif state == 'setCustomLocationName':
            client.messages.create(to=to_num, from_=from_num,body='What is location of "' + body.lower() + '"?')
            session['state'] = 'setCustomLocation'
            session['locationVarName'] = body.lower()
        elif state == 'setCustomLocation':
            var = session.get('locationVarName', '')
            loc = check_location(body)
            print('jsgdfgsfkjhgasljhdfglajhsgfdjlhsagdfjagsdkjhfgaskjhdfgjhasd')
            print(loc)
            if var != '' and loc != '':
                session['locationVarLocation'] = loc
                confirmloc = "Please confirm this is your location: " + loc
                client.messages.create(to=to_num, from_=from_num,body=confirmloc)
                session['state'] = 'confirmCustomLocation'
            else:
                session['locationVarName'] = ''
                session['locationVarLocation'] = ''
                clearConversationState()
                client.messages.create(to=to_num, from_=from_num,body='Error creating custom location. Please try again.')
            return ''
        elif state == 'confirmCustomLocation':
            var = session.get('locationVarName', '')
            loc = session.get('locationVarLocation', '')
            if var != '' and loc != '' and checkConfirm(body):
                customLoc = {'name': var, 'location': loc}
                customLocations = json.loads(session.get('customLocations', defaultLocations))
                customLocations['locations'].append(customLoc)
                session['customLocations'] = json.dumps(customLocations)
                client.messages.create(to=to_num, from_=from_num,body='Set custom location "' + var + '" with value of "' + loc + '".')
                session['locationVarName'] = ''
                session['locationVarLocation'] = ''
                clearConversationState()
            else: 
                client.messages.create(to=to_num, from_=from_num,body='Okay, What is location of "' + var + '"?')
                session['state'] = 'getCustomLocation'
                session['locationVarLocation'] = ''
            return ''
        else:
            checkLocations = 1
        
        if checkLocations == 1:
            if locations.toLoc == '':
                session['state'] = 'getTo'
                wheretogo = "Okay, Where do you want to go?"
                client.messages.create(to=to_num, from_=from_num,body=wheretogo)
            elif confirmedTo == 0:
                if (checkConfirm(body)):
                    confirmedTo = 1
                    session['confirmed_to'] = confirmedTo
                    checkLocations = 1
                else:
                    session['state'] = 'getTo'
                    wheretogo = "Okay, where do you want to go?"
                    client.messages.create(to=to_num, from_=from_num,body=wheretogo)
            elif locations.fromLoc == '':
                session['state'] = 'getFrom'
                whereareyou = "Okay, Where are you?"
                client.messages.create(to=to_num, from_=from_num,body=whereareyou)
            elif confirmedFrom  == 0:
                session['state'] = 'confirmFrom'
                confirmfrom = "Please confirm this is where you are coming from: " + locations.fromLoc
                client.messages.create(to=to_num, from_=from_num,body=confirmfrom)
            else:
                directions = parse_directions(locations)
                routinglocation = "Sending directions from " + directions.start + " to " + directions.end + " by " + locations.mode + ".\nTime: " + directions.time
                client.messages.create(to=to_num, from_=from_num,body=routinglocation)
                client.messages.create(to=to_num, from_=from_num,body=directions.steps)
                session['state'] = 'new'
                session['to_location'] = ''
                session['from_location'] = ''
                session['transport_mode'] = ''
                session['message_time'] = ''
                session['confirmed_to'] = 0
                session['confirmed_from'] = 0
                client.messages.create(to=to_num, from_=from_num,body='Done!')

    print('Message: ' + body)
    print('State: ' + state)
    print('From: ' + locations.fromLoc + (' confirmed' if (confirmedTo == 1) else ' not confirmed'))
    print('To: ' + locations.toLoc + (' confirmed' if (confirmedFrom == 1) else ' not confirmed'))
    print('Mode: ' + locations.mode)
    return ''

def cleanup_message(step):
    step.replace("<b>","")
    step.replace("</b>", "")
    step.replace("<div>", "")
    step.replace("</div>","")
    return step


def send_direction(steps, from_num, to_num):
        message = client.messages.create(to=to_num, from_=from_num,
                                         body=steps)
def get_directions(loc_from, loc_to, transport):
    directions = []

    now = datetime.datetime.now()
    directions_result = gmaps.directions(loc_from,
                                         loc_to,
                                         mode=transport,
                                         departure_time=now)

    return directions_result

def clearConversationState():
    session['state'] = 'new'
    session['to_location'] = ''
    session['from_location'] = ''
    session['transport_mode'] = ''
    session['confirmed_to'] = 0
    session['confirmed_from'] = 0


if __name__ == "__main__":
    app.run(debug=True)