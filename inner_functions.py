import requests
import json
from tokens import GOOGLE_API_KEY
import re

def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    if direction == 'S' or direction == 'W':
        dd *= -1
    return dd;


def get_latlong(incoming_text):
    parts = re.split("[^\d\w]+", incoming_text)
    lat = dms2dd(parts[0],parts[1],parts[2],parts[3])
    lng = dms2dd(parts[4],parts[5],parts[6],parts[7])

    return lat, lng


def get_locations(incoming_text):
    data={"document":{"type":"PLAIN_TEXT","content":incoming_text},"encodingType":"UTF16"}

    r=requests.post("https://language.googleapis.com/v1beta2/documents:analyzeEntities?key=" + GOOGLE_API_KEY, json=data)
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
            #print(entities["name"])
            if entities["name"] == "driving" or entities["name"] == "drive":
                mode = "driving"
            if entities["name"] == "walking" or entities["name"] == "walk":
                mode = "walking"
            if entities["name"] == "bicycling" or entities["name"] == "bike":
                mode = "bicycling"
            if entities["name"] == "transit" or entities["name"] == "train" or entities["name"] == "bus":
                mode = "transit"

    locations = locationsClass()
    locations.fromLoc = check_location(fromLoc)
    locations.toLoc = check_location(toLoc)
    locations.mode = mode
    return locations

def parse_directions(locations):

    response=requests.get("https://maps.googleapis.com/maps/api/directions/json?origin=" + locations.fromLoc + "&destination=" + locations.toLoc + "&mode=" + locations.mode + "&key=" + GOOGLE_API_KEY + "&region=ca")

    unparsed=response.json()

    directions = directionsClass()
    directions.time = unparsed["routes"][0]["legs"][0]["duration"]["text"]
    directions.to = unparsed["routes"][0]["legs"][0]["end_address"]
    directions.start = unparsed["routes"][0]["legs"][0]["start_address"]
    stepNum = 1
    messageNum = 0
    for step in unparsed["routes"][0]["legs"][0]["steps"]:
        direction = step["html_instructions"].replace('<b>','').replace('</b>','')
        newStep = str(stepNum) + '. ' + direction + '\n'
        if (len(directions.steps[messageNum]) + len(newStep)) < 1450:
            directions.steps[messageNum] += newStep
        else:
            messageNum += 1
            directions.steps.append('')
            directions.steps[messageNum] += newStep
        stepNum += 1

    return directions

class directionsClass:
    start = ''
    end = ''
    time = ''
    steps = ['']

class locationsClass:
    fromLoc = ''
    toLoc = ''
    mode = ''

def autocomplete_location(location):
    r = requests.get(
        "https://maps.googleapis.com/maps/api/place/autocomplete/json?key=" + GOOGLE_API_KEY + "&input=" + location+"&region=ca")
    testing = json.loads(r.text)
    if (testing['status'] == 'ZERO_RESULTS'):
        return ''
    description = testing["predictions"][0]["description"]
    return description

def check_location(location):
    r = requests.get(
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?key=" + GOOGLE_API_KEY + "&input=" + location + "&inputtype=textquery"+"&region=ca"+"&fields=geometry,formatted_address,place_id")
    testing = json.loads(r.text)
    #print("this is testing geo", testing)
    candidates = testing["candidates"]

    questionAddress = ''
    if(testing["status"] == "ZERO_RESULTS"):
        autoAddress = autocomplete_location(location)
        questionAddress = autoAddress
    else:
        for place in candidates:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/place/details/json?key=" + GOOGLE_API_KEY + "&placeid=" + place["place_id"])
            ploop = json.loads(r.text)
            #print(ploop)
            questionAddress = ploop["result"]["formatted_address"]

    return questionAddress
