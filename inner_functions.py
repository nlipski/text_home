import requests
import json
import re 
from tokens import GOOGLE_API_KEY

def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)
    if direction == 'S' or direction == 'W':
        dd *= -1
    return dd


def parse_dms(dms):
    try:
        parts = re.split('[^\d\w]+', dms)
        lat = dms2dd(parts[0], parts[1], parts[2], parts[3])
        lng = dms2dd(parts[4], parts[5], parts[6], parts[7])
        return lat, lng
    except:
        return "", ""


def checkgeo_location(body):
    lat, lng = parse_dms(body)
    if lat != "" and lng != "":
        r = requests.get("https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(lat) + "," + str(lng) + "&key=" + GOOGLE_API_KEY)
        testing = json.loads(r.text)
        fromLoc = testing["results"][0]["formatted_address"]
    else:
        fromLoc = check_location(body)

    return fromLoc


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
            print(entities["name"])
            if entities["name"] == "driving" or entities["name"] == "drive":
                mode = "driving"
            if entities["name"] == "walking" or entities["name"] == "walk":
                mode = "walking"
            if entities["name"] == "bicycling" or entities["name"] == "bike":
                mode = "bicycling"
            if entities["name"] == "transit" or entities["name"] == "train" or entities["name"] == "bus":
                mode = "transit"

    locations = locationsClass()
    if fromLoc != '':
        locations.fromLoc = check_location(fromLoc)
    else:
        locations.fromLoc = ''

    if toLoc != '':
        locations.toLoc = check_location(toLoc)
    else:
        locations.toLoc = ''

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
    directions.steps = ['']
    for step in unparsed["routes"][0]["legs"][0]["steps"]:
        #direction = step["html_instructions"].replace('<b>','').replace('</b>','')
        #direction = re.sub("<.*?>", " ", direction)
        direction = html_tag_remover(step["html_instructions"])
        line = str(stepNum) + '. ' + direction + '\n'
        if len(directions.steps[messageNum]) + len(line) > 1000:
            directions.steps.append('')
            messageNum += 1
        directions.steps[messageNum] += line
        stepNum += 1

    return directions

def html_tag_remover(line):
    while (line.find('<') != -1 and  line.find('>') != -1):
        line= line[:line.find('<')] + line[line.find('>')+1:]
    print(line)
    return line

class directionsClass:
    start = ''
    end = ''
    time = ''
    steps = ''

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
    print('location' + location)
    r = requests.get(
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?key=" + GOOGLE_API_KEY + "&input=" + location + "&inputtype=textquery")#+"&region=ca")#+"&fields=geometry,formatted_address,place_id")
    testing = json.loads(r.text)
    print("this is testing geo",testing)
    candidates = testing["candidates"]
    print(r.text)

    questionAddress = ''
    if(testing["status"] == "ZERO_RESULTS"):
        questionAddress = autocomplete_location(location)
    else:
        r = requests.get(
                "https://maps.googleapis.com/maps/api/place/details/json?key=" + GOOGLE_API_KEY + "&placeid=" + candidates[0]["place_id"])
        ploop = json.loads(r.text)
        geocoord= ploop["result"]["geometry"]["location"]
        questionAddress = ploop["result"]["formatted_address"]
        print( questionAddress  )
        print ( geocoord)

    return questionAddress
