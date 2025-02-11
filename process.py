import json
from operator import ge
import requests
import sys
from datetime import datetime



def get_data(flight_id: str, timestamp="") -> dict:
    # request flight info from Flightradar24 api
    # return dict
    if timestamp:
        url = f"https://api.flightradar24.com/common/v1/flight-playback.json?flightId={flight_id}&timestamp={timestamp}"
    else:
        url = f"https://api.flightradar24.com/common/v1/flight-playback.json?flightId={flight_id}"

    payload = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.status_code)

    return json.loads(response.text)


## prepare geoJSON output
geoJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": []},
            "properties": {},
        }
    ],
}

if len(sys.argv) < 2:
    print("Provide at least flight_id")
    sys.exit()


## input parameters
flight_id = sys.argv[1]
timestamp=""
if len(sys.argv) == 3:
    scheduled_departure = sys.argv[2]
    dt = datetime.strptime(scheduled_departure, "%d/%m/%Y-%H:%M")
    timestamp = int(dt.timestamp())
    print(timestamp)

data = get_data(flight_id, timestamp)
max_heigth = 0
max_speed = 0


# get track data
track = data["result"]["response"]["data"]["flight"]["track"]
geoJSON["features"][0]["properties"]["flightId"] = flight_id
geoJSON["features"][0]["properties"]["timestamp"] = timestamp
geoJSON["features"][0]["properties"]["status"] = data["result"]["response"]["data"]["flight"]["status"]["generic"]
geoJSON["features"][0]["properties"]["aircraft"] = data["result"]["response"]["data"]["flight"]["aircraft"]["model"]["text"]
geoJSON["features"][0]["properties"]["airportOrigin"] = data["result"]["response"]["data"]["flight"]["airport"]["origin"]["name"]
geoJSON["features"][0]["properties"]["airportDestination"] = data["result"]["response"]["data"]["flight"]["airport"]["destination"]["name"]


# get origin and destination IATA codes
origin = data["result"]["response"]["data"]["flight"]["airport"]["origin"]["code"]["iata"]
destination = data["result"]["response"]["data"]["flight"]["airport"]["destination"]["code"]["iata"]

# put coordinate pairs in output dict
for obj in track:
    speed = obj["speed"]["kmh"]

    geoJSON["features"][0]["geometry"]["coordinates"].append(
        [obj["longitude"], obj["latitude"], obj["altitude"]["meters"]]
    )
    if obj["altitude"]["meters"] > max_heigth:
        max_heigth = obj["altitude"]["meters"]
    if speed > max_speed:
        max_speed = speed

number = data["result"]["response"]["data"]["flight"]["identification"]["number"]["default"]
geoJSON["features"][0]["properties"]["maxSpeed"] = max_speed
geoJSON["features"][0]["properties"]["maxHeight"] = max_heigth
geoJSON["features"][0]["properties"]["name"] = f'{number}: {origin} -> {destination}'

# make json
json_object = json.dumps(geoJSON, indent=4)

# write to file
with open(f"track_{origin}-{destination}{datetime.now().strftime('%Y%M%d_%H%M%S')}.json", "w") as outfile:
    outfile.write(json_object)


with open( f"track_{origin}-{destination}{datetime.now().strftime('%Y%M%d_%H%M%S')}.gpx", "w") as gpxfile:
    gpxfile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    gpxfile.write('''<gpx version="1.0"
     creator="Totot Jatotrava"
     xmlns="http://www.topografix.com/GPX/1/0"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">\n''')
    gpxfile.write(f'''<desc>Aircraft: {data["result"]["response"]["data"]["flight"]["aircraft"]["model"]["text"]}; max_speed: {max_speed}</desc>\n''')
    gpxfile.write("<keywords>flight</keywords>\n")
    gpxfile.write(f"<trk><name>{number}: {origin} -> {destination}'</name>\n<trkseg>\n")
    for obj in track:
           speed = obj["speed"]["kmh"]/3.6
           lat = obj["latitude"]
           lon = obj["longitude"]
           alt = obj["altitude"]["meters"]
           course = obj["heading"]
           t = obj["timestamp"]
           time = datetime.utcfromtimestamp(t).isoformat()
           gpxfile.write(f'<trkpt lat="{lat}" lon="{lon}"><ele>{alt}</ele><speed>{speed}</speed><course>{course}</course><time>{time}</time></trkpt>\n')


    gpxfile.write("</trkseg>\n</trk>\n</gpx>\n")    


