from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, session
import googlemaps
from inner_functions import get_locations, check_location, parse_directions, locationsClass
from default_classes import storedLocationClass
from state_functions import defaultLocations, setLocation, getLocations, removeLocations, getTo, setGetTo, confirmTo, getFrom, setGetFrom, confirmFrom, clearConversationState, getHelp, checkConfirm
from tokens import client, GOOGLE_API_KEY
import datetime
import json
import os

SECRET_KEY = os.environ['SECRET_KEY']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
TWILIO_ACCOUNT = os.environ['TWILIO_ACCOUNT']
TWILIO_TOKEN = os.environ['TWILIO_TOKEN']

client = Client(TWILIO_ACCOUNT, TWILIO_TOKEN)

app = Flask(__name__)
app.config.from_object(__name__)

gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

def html_tag_remover(line):
    strart =-1
    end = -1
    while (line.find('<') != -1 and  line.find('>') != -1):
        line= line[:line.find('<')] + line[line.find('>')+1:]
    return line


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
        getHelp(body, to_num, from_num)
        return ''
    elif body.lower().startswith('set-location'):
        setLocation(body, to_num, from_num)
        return ''
    elif body.lower() == 'get-locations':
        getLocations(body, to_num, from_num)
        return ''
    elif body.lower() == 'remove-locations':
        removeLocations(body, to_num, from_num)
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
            locations.toLoc = getTo(body, to_num, from_num)
        elif state == 'getFrom':
            locations.fromLoc = getFrom(body, to_num, from_num
            )
        elif state == 'confirmTo':
            if (confirmTo(body, to_num, from_num)):
                confirmedTo = 1
                checkLocations = 1
        elif state == 'confirmFrom':
            if (confirmFrom(body, to_num, from_num)):
                confirmedFrom = 1
                checkLocations = 1
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
                print('a')
                setGetTo(body, to_num, from_num)
            elif confirmedTo == 0:
                print('b')
                confirmTo(body, to_num, from_num)
            elif locations.fromLoc == '':
                print('c')
                setGetFrom(body, to_num, from_num)
            elif confirmedFrom  == 0:
                print('d')
                confirmFrom(body, to_num, from_num)
            else:
                directions = parse_directions(locations)
                routinglocation = "Sending directions from " + directions.start + " to " + directions.end + " by " + locations.mode + ".\nTime: " + directions.time
                client.messages.create(to=to_num, from_=from_num,body=routinglocation)
                for step in directions.steps:
                    step = html_tag_remover(step)
                    client.messages.create(to=to_num, from_=from_num,body=step)
                session['state'] = 'new'
                session['to_location'] = ''
                session['from_location'] = ''
                session['transport_mode'] = ''
                session['message_time'] = ''
                session['confirmed_to'] = 0
                session['confirmed_from'] = 0
                client.messages.create(to=to_num, from_=from_num,body='Done!')

    print('Message: ' + body)
    print('From Number: ' + from_num + ' To Number: ' + to_num)
    print('State: ' + state)
    print('From: ' + locations.fromLoc + (' confirmed' if (confirmedTo == 1) else ' not confirmed'))
    print('To: ' + locations.toLoc + (' confirmed' if (confirmedFrom == 1) else ' not confirmed'))
    print('Mode: ' + locations.mode)
    return ''


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


if __name__ == "__main__":
    app.run(debug=True)