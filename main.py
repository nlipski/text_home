from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, session
import googlemaps
import json
import requests
import datetime

SECRET_KEY = 'a secret key'
app = Flask(__name__)
app.config.from_object(__name__)

google_api_key="AIzaSyBUlQyHBJsv-GBooA_64cyA_9q-abYSehE"

gmaps = googlemaps.Client(key=google_api_key)

account = "ACd6f3f6f499dc943cbca7ee0ce16aff6e"
token = "8377bf56ca922921e9b61547d951c018"
client = Client(account, token)


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    body = request.values.get('Body', None)
    to_num = request.values.get('From', None)
    from_num = request.values.get('To', None)

    if body.lower() == 'clear session' or body.lower() == 'clear':
        session['state'] = 'new'
        session['to_location'] = ''
        session['from_location'] = ''
        session['transport_mode'] = ''
        session['message_time'] = ''
        session['confirmed_to'] = 0
        session['confirmed_from'] = 0
        client.messages.create(to=to_num, from_=from_num,body='Session cleared successfully!')
        return ''
    else:
        state = session.get('state', 'new')
        lastTime = session.get('message_time', '')
        now = datetime.datetime.now()
        FMT = '%d-%m-%Y_%H:%M:%S'
        session['message_time'] = now.strftime(FMT)

        confirmedTo = session.get('confirmed_to', 0)
        confirmedFrom = session.get('confirmed_from', 0)

        if lastTime == '':
            toLoc = ''
            fromLoc = ''
            mode = ''
            session['state'] = 'new'
            state = 'new'
        else:
            timeDiff = now - datetime.datetime.strptime(lastTime, FMT)
            print("time diff: " + str(timeDiff))
            if timeDiff < datetime.timedelta(minutes=5):
                toLoc = session.get('to_location', '')
                fromLoc = session.get('from_location', '')
                mode = session.get('transport_mode', '')
            else:
                toLoc = ''
                fromLoc = ''
                mode = ''
                session['state'] = 'new'
                state = 'new'

        checkLocations = 0
        if state == 'new':
            locations = get_locations(body)
            fromLoc = check_location(locations[0])
            toLoc = check_location(locations[1])
            mode = locations[2]
            session['to_location'] = toLoc
            session['from_location'] = fromLoc
            session['transport_mode'] = mode
            print('From: ' + fromLoc)
            print('To: ' + toLoc)
            print('Mode: ' + mode)
            checkLocations = 1
        elif state == 'getTo':
            toLoc = check_location(body)
            session['to_location'] = toLoc
            session['state'] = 'confirmTo'
            confirmto = "Please confirm this is your destination: " + toLoc
            client.messages.create(to=to_num, from_=from_num,body=confirmto)
        elif state == 'getFrom':
            fromLoc = check_location(body)
            session['from_location'] = fromLoc
            session['state'] = 'confirmFrom'
            confirmfrom = "Please confirm this is where you are coming from: " + fromLoc
            client.messages.create(to=to_num, from_=from_num,body=confirmfrom)
        elif state == 'confirmTo':
            if (body.lower() == 'yes' or body.lower() == 'y'):
                confirmedTo = 1
                session['confirmed_to'] = confirmedTo
                checkLocations = 1
            else:
                session['state'] = 'getTo'
                wheretogo = "Okay, where do you want to go?"
                client.messages.create(to=to_num, from_=from_num,body=wheretogo)
        elif state == 'confirmFrom':
            if (body.lower() == 'yes' or body.lower() == 'y'):
                confirmedFrom = 1
                session['confirmed_from'] = confirmedFrom
                checkLocations = 1
            else:
                session['state'] = 'getFrom'
                wheretogo = "Okay, where are you?"
                client.messages.create(to=to_num, from_=from_num,body=wheretogo)
        else:
            checkLocations = 1
        
        if checkLocations == 1:
            if toLoc == '':
                session['state'] = 'getTo'
                wheretogo = "Okay, Where do you want to go?"
                client.messages.create(to=to_num, from_=from_num,body=wheretogo)
            elif confirmedTo == 0:
                session['state'] = 'confirmTo'
                confirmto = "Please confirm this is your destination: " + toLoc
                client.messages.create(to=to_num, from_=from_num,body=confirmto)
            elif fromLoc == '':
                session['state'] = 'getFrom'
                whereareyou = "Okay, Where are you?"
                client.messages.create(to=to_num, from_=from_num,body=whereareyou)
            elif confirmedFrom  == 0:
                session['state'] = 'confirmFrom'
                confirmfrom = "Please confirm this is where you are coming from: " + fromLoc
                client.messages.create(to=to_num, from_=from_num,body=confirmfrom)
            else:
                routinglocation = "Sending directions from " + fromLoc + " to " + toLoc + " by " + mode
                client.messages.create(to=to_num, from_=from_num,body=routinglocation)
                #steps = parse_directions(fromLoc, toLoc, mode)
                #send_direction(steps, from_num, to_num)
                session['state'] = 'new'
                session['to_location'] = ''
                session['from_location'] = ''
                session['transport_mode'] = ''
                session['message_time'] = ''
                session['confirmed_to'] = 0
                session['confirmed_from'] = 0
                client.messages.create(to=to_num, from_=from_num,body='Done!')
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
            print(entities["name"])
            if entities["name"] == "driving" or entities["name"] == "drive":
                mode = "driving"
            if entities["name"] == "walking" or entities["name"] == "walk":
                mode = "walking"
            if entities["name"] == "bicycling" or entities["name"] == "bike":
                mode = "bicycling"
            if entities["name"] == "transit" or entities["name"] == "train" or entities["name"] == "bus":
                mode = "transit"

    return [fromLoc, toLoc, mode]

def parse_directions(fromLoc, toLoc, mode):

    response=requests.get("https://maps.googleapis.com/maps/api/directions/json?origin=" + fromLoc + "&destination=" + toLoc + "&mode=" + mode + "&key=" + google_api_key)

    unparsed=response.json()

    time = unparsed["routes"][0]["legs"][0]["duration"]["text"]
    to =unparsed["routes"][0]["legs"][0]["end_address"]
    start =unparsed["routes"][0]["legs"][0]["start_address"]
    directions = []
    for step in unparsed["routes"][0]["legs"][0]["steps"]: 
        direction = step["html_instructions"].replace('<b>','').replace('</b>','')
        directions.append(direction)
    returntext= "Here are your instructions from",(start),"to" ,(to), ". It will take",(time),  (directions)


    return returntext

def autocomplete_location(location):
    r = requests.get(
        "https://maps.googleapis.com/maps/api/place/autocomplete/json?key=" + google_api_key + "&input=" + location);
    testing = json.loads(r.text)
    if (testing['status'] == 'ZERO_RESULTS'):
        return ''
    description = testing["predictions"][0]["description"]
    return description

def check_location(location):
    r = requests.get(
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?key=" + google_api_key + "&input=" + location + "&inputtype=textquery");
    testing = json.loads(r.text)
    candidates = testing["candidates"]

    questionAddress = ''
    if(testing["status"] == "ZERO_RESULTS"):
        autoAddress = autocomplete_location(location)
        questionAddress = autoAddress
    else:
        for place in candidates:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/place/details/json?key=" + google_api_key + "&placeid=" + place["place_id"])
            ploop = json.loads(r.text)
            questionAddress = ploop["result"]["formatted_address"]

    return questionAddress


if __name__ == "__main__":
    app.run(debug=True)