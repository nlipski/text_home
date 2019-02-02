from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, session
import googlemaps
import json
import requests
from datetime import datetime

SECRET_KEY = 'a secret key'
app = Flask(__name__)
app.config.from_object(__name__)

google_api_key="AIzaSyBUlQyHBJsv-GBooA_64cyA_9q-abYSehE"

gmaps = googlemaps.Client(key=google_api_key)

account = "AC07e3abdcc5ca8ab68816022080fb9331"
token = "e50d782ec9b8c284db8ab0f537ed0fbc"
client = Client(account, token)


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    body = request.values.get('Body', None)
    to_num = request.values.get('From', None)
    from_num = request.values.get('To', None)

    counter = session.get('counter', 0)
    counter += 1

    state = session.get('state', 'new')
    lastTime = session.get('message_time', '')
    now = datetime.now()
    FMT = '%H:%M:%S'
    session['message_time'] = now.strftime(FMT)
    timeDiff = now - datetime.strptime(lastTime, FMT)
    maxDiff = now.replace(hour=0, minute=5, second=0, microsecond=0)
    if timeDiff < maxDiff:
        toLoc = session.get('to_location', '')
        fromLoc = session.get('from_location', '')
        mode = session.get('transport_mode', '')
    else:
        toLoc = ''
        fromLoc = ''
        mode = ''
        session['state'] = 'new'
        state = 'new'

    locations = get_locations(body)
    if state == 'new':
        fromLoc = locations[0]
        toLoc = locations[1]
        mode = locations[2]
    elif state == 'getTo':
        toLoc = locations[0]
    elif state == 'getFrom':
        fromLoc = locations[0]
    elif state == 'getMode':
        mode = locations[2]
    
    if toLoc == '':
        session['state'] = 'getTo'
        print('getTo')
        wheretogo = "Unfortunately we did not get where you wanted to go. Where do you want to go?"
        client.messages.create(to=to_num, from_=from_num,body=wheretogo)
    elif fromLoc == '':
        session['state'] = 'getFrom'
        print('getFrom')
        whereareyou = "Unfortunately we did not get where you are. Where are you?"
        client.messages.create(to=to_num, from_=from_num,body=whereareyou)
    elif mode == '':
        session['state'] = 'getMode'
        print('getMode')
        whereareyou = "Unfortunately we did not get how you want to get there. How do you want to do that?"
        client.messages.create(to=to_num, from_=from_num,body=whereareyou)
    else:
        client.messages.create(to=to_num, from_=from_num,body="STOP BEING DUMB")

    steps = parse_directions(locations[0], locations[1], locations[2])

    send_direction(steps, from_num, to_num)
    
    resp = MessagingResponse()
    resp.message("Done")

    return str(resp)

def cleanup_message(step):
    step.replace("<b>","")
    step.replace("</b>", "")
    step.replace("<div>", "")
    step.replace("</div>","")
    return step


def send_direction(steps, from_num, to_num):
    for step in steps:
        line = "For " + step["distance"]["text"] + " " + step["html_instructions"]
        line = cleanup_message(line)
        message = client.messages.create(to=to_num, from_=from_num,
                                         body=line)
def get_directions(loc_from, loc_to, transport):
    directions = []

    now = datetime.now()
    directions_result = gmaps.directions(loc_from,
                                         loc_to,
                                         mode=transport,
                                         departure_time=now)

    return directions_result

def get_locations(incoming_text):
    data={"document":{"type":"PLAIN_TEXT","content":incoming_text},"encodingType":"UTF16"}

    r=requests.post("https://language.googleapis.com/v1beta2/documents:analyzeEntities?key=" + google_api_key, json=data)
    testing = json.loads(r.text)
    testbla = testing["entities"]

    toLoc = ""
    fromLoc = ""
    mode = "driving"
    for entities in testbla:
        if entities["type"] == "LOCATION":
            index = int(entities["mentions"][0]["text"]["beginOffset"])
            reference = incoming_text[index - 3:index]
            if reference == "to ":
                toLoc = entities["name"]
            else:
                fromLoc = entities["name"]
        elif entities["type"] == "OTHER":
            if entities["name"] == "driving" or entities["name"] == "drive":
                mode = "driving"
            if entities["name"] == "walking" or entities["name"] == "walk":
                mode = "walking"
            if entities["name"] == "bicycling" or entities["name"] == "bike":
                mode = "bicycling"
            if entities["name"] == "transit":
                mode = "transit"

    if len(fromLoc) <= 1 and len(toLoc) <= 1:
        return 0

    return [fromLoc, toLoc, mode ]

def parse_directions(fromLoc, toLoc, mode):

    r=requests.get("https://maps.googleapis.com/maps/api/directions/json?origin=" + fromLoc + "&destination=" + toLoc + "&mode=" + mode + "&key=" + google_api_key)
    testing = json.loads(r.text)

    something = testing["routes"]
    some = something[0]
    steps = some["legs"][0]["steps"]

    return steps


if __name__ == "__main__":
    app.run(debug=True)