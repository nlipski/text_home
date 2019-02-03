from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, session
import googlemaps
from inner_functions import get_locations, check_location, parse_directions, locationsClass
from default_classes import storedLocationClass, defaultCustomLocations
from state_functions import setLocation, setCustomLocationName, setCustomLocationLocation, confirmCustomLocation, getLocations, removeLocations, getTo, setGetTo, confirmTo, getFrom, setGetFrom, confirmFrom, clearConversationState, getHelp, sendLocationHelp, sendThanks, checkConfirm
from tokens import client, GOOGLE_API_KEY, SECRET_KEY
import datetime
import json
import os

# SECRET_KEY = os.environ['SECRET_KEY']
# GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
# TWILIO_ACCOUNT = os.environ['TWILIO_ACCOUNT']
# TWILIO_TOKEN = os.environ['TWILIO_TOKEN']

# client = Client(TWILIO_ACCOUNT, TWILIO_TOKEN)

app = Flask(__name__)
app.config.from_object(__name__)

gmaps = googlemaps.Client(key=GOOGLE_API_KEY)


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    print('I AM ACTUALLY DOING SHIT')
    body = request.values.get('Body', None)
    to_num = request.values.get('From', None)
    from_num = request.values.get('To', None)
    print(request.values.get('subresource_uris', None))

    print('\n\n------------------START-------------------------')
    print('Message: ' + body)
    print('From Number: ' + from_num + ' To Number: ' + to_num)
    print('State: ' + session.get('state', ''))
    print('From: ' + session.get('from_location', '') + (' confirmed' if (session.get('confirmed_from', 0) == 1) else ' not confirmed'))
    print('To: ' + session.get('to_location', '') + (' confirmed' if (session.get('confirmed_to', 0) == 1) else ' not confirmed'))
    print('Mode: ' + session.get('mode', ''))

    if body.lower() == 'clear session' or body.lower() == 'clear' or body.lower() == 'reset':
        clearConversationState()
        client.messages.create(to=to_num, from_=from_num,body='Session cleared successfully!')
        return ''
    elif body.lower() == 'clear-all':
        session.clear()
        client.messages.create(to=to_num, from_=from_num,body='Session cleared successfully!')
        return ''
    elif body.lower() == 'where am i':
        sendLocationHelp(body, to_num, from_num)
        return ''
    elif body.lower() == 'map-help' or body.lower() == 'idk':
        getHelp(body, to_num, from_num)
        return ''
    elif body.lower() == 'thanks' or body.lower() == 'thank you':
        sendThanks(body, to_num, from_num)
        return ''
    elif body.lower().startswith('set-location'):
        clearConversationState()
        setLocation(body, to_num, from_num)
        return ''
    elif body.lower() == 'get-locations':
        clearConversationState()
        getLocations(body, to_num, from_num)
        return ''
    elif body.lower() == 'remove-locations':
        clearConversationState()
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
            session['state'] = 'continue'
            session['to_location'] = locations.toLoc
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
            setCustomLocationName(body, to_num, from_num)
            return ''
        elif state == 'setCustomLocationLocation':
            setCustomLocationLocation(body, to_num, from_num)
            return ''
        elif state == 'confirmCustomLocation':
            confirmCustomLocation(body, to_num, from_num)
            return ''
        else:
            checkLocations = 1
        
        if checkLocations == 1:
            if locations.toLoc == '':
                setGetTo(body, to_num, from_num)
            elif confirmedTo == 0:
                session['state'] = 'confirmTo'
                confirmto = "Please confirm this is your destination " + locations.toLoc
                client.messages.create(to=to_num, from_=from_num,body=confirmto)
            elif locations.fromLoc == '':
                setGetFrom(body, to_num, from_num)
            elif confirmedFrom  == 0:
                session['state'] = 'confirmFrom'
                confirmfrom = "Please confirm this is where you are coming from: " + locations.fromLoc
                client.messages.create(to=to_num, from_=from_num,body=confirmfrom)
            else:
                directions = parse_directions(locations)
                routinglocation = "Sending directions from " + directions.start + " to " + directions.end + " by " + locations.mode + ".\nTime: " + directions.time
                client.messages.create(to=to_num, from_=from_num,body=routinglocation)
                for step in directions.steps:
                    client.messages.create(to=to_num, from_=from_num,body=step)
                session['state'] = 'new'
                session['to_location'] = ''
                session['from_location'] = ''
                session['transport_mode'] = ''
                session['message_time'] = ''
                session['confirmed_to'] = 0
                session['confirmed_from'] = 0
                client.messages.create(to=to_num, from_=from_num,body='Done!')
    return ''


if __name__ == "__main__":
    app.run(debug=True)