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

    state = session.get('state', 'new')
    print('initial state: ' + state)
    lastTime = session.get('message_time', '')
    now = datetime.datetime.now()
    FMT = '%d-%m-%Y_%H:%M:%S'
    session['message_time'] = now.strftime(FMT)
    print(now.strftime(FMT))

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

    locations = get_locations(body)
    print(state)
    if state == 'new':
        fromLoc = locations[0]
        toLoc = locations[1]
        mode = locations[2]
    elif state == 'getTo':
        toLoc = locations[0]
        session['to_location'] = toLoc
        session['state'] = 'confirmTo'
        print(toLoc)
    elif state == 'getFrom':
        fromLoc = locations[0]
        session['from_location'] = fromLoc
        session['state'] = 'confirmFrom'
        print(fromLoc)
    elif state == 'getMode':
        mode = locations[2]
        session['transport_mode'] = mode
        session['state'] = 'confirmMode'
        print(mode)
    
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
        steps = parse_directions(locations[0], locations[1], locations[2])
        send_direction(steps, from_num, to_num)
        resp = MessagingResponse()
        resp.message("Done")
        return str(resp)
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
            if entities["name"] == "driving" or entities["name"] == "drive":
                mode = "driving"
            if entities["name"] == "walking" or entities["name"] == "walk":
                mode = "walking"
            if entities["name"] == "bicycling" or entities["name"] == "bike":
                mode = "bicycling"
            if entities["name"] == "transit":
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

    description = testing["predictions"][0]["description"]
    return description

def check_location(location):
    r = requests.get(
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?key=" + google_api_key + "&input=" + location + "&inputtype=textquery");
    testing = json.loads(r.text)
    candidates = testing["candidates"]

    if(testing["status"] == "ZERO_RESULTS"):
        autoAddress = autocomplete_location(location)
        print("Did you mean to type " + autoAddress + "?")
        questionAddress = autoAddress
    else:
        for place in candidates:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/place/details/json?key=" + google_api_key + "&placeid=" + place["place_id"])
            ploop = json.loads(r.text)
            questionAddress = ploop["result"]["formatted_address"]
            print("Did you mean " + questionAddress + "?")

    return questionAddress


if __name__ == "__main__":
    app.run(debug=True)