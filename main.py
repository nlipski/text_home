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

    locations = get_locations(body)
    print (locations)

    steps = parse_directions(locations[0], locations[1])

    message = ""
    send_direction(steps, from_num, to_num)
    resp = MessagingResponse()
    resp.message(message)

    return str(resp)

def send_direction(steps, from_num, to_num):
    for step in steps:

        line = "For " + step["distance"]["text"] + " " + step["html_instructions"]
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
    loc1 = ""
    loc2 = ""
    for entities in testbla:
        if entities["type"] == "LOCATION":
            if loc1 == "":
                loc1 = entities["name"]
            elif loc2 == "":
                loc2 = entities["name"]
    print (loc1)
    print(loc2)
    return [loc1, loc2]

def parse_directions(loc1, loc2):
    r=requests.get("https://maps.googleapis.com/maps/api/directions/json?origin=" + loc1 + "&destination=" + loc2 + "&key=" + google_api_key)
    testing = json.loads(r.text)

    something = testing["routes"]
    some = something[0]
    steps = some["legs"][0]["steps"]

    return steps


if __name__ == "__main__":
    app.run(debug=True)
print(message.sid)