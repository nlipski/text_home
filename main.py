from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request, session
import googlemaps
import json
import requests
from datetime import datetime


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

    resp = MessagingResponse()
    locations = get_locations(body)
    if locations == 0:
        resp.message("STOP BEING DUMB")
        return str(resp)
    steps = parse_directions(locations[0], locations[1], locations[2])

    send_direction(steps, from_num, to_num)
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
print(message.sid)