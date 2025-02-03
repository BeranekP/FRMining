import json
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
output = {
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
    time = sys.argv[2]
    dt = datetime.strptime(time, "%d/%m/%Y-%H:%M:%S")
    timestamp = dt.timestamp()
    print(timestamp)

data = get_data(flight_id, timestamp)

# get track data
track = data["result"]["response"]["data"]["flight"]["track"]


# get origin and destination IATA codes
origin = data["result"]["response"]["data"]["flight"]["airport"]["origin"]["code"]["iata"]
destination = data["result"]["response"]["data"]["flight"]["airport"]["destination"]["code"]["iata"]

# put coordinate pairs in output dict
for obj in track:
    output["features"][0]["geometry"]["coordinates"].append(
        [obj["longitude"], obj["latitude"]]
    )

# make json
json_object = json.dumps(output, indent=4)

# write to file
with open(f"track {origin}-{destination}.json", "w") as outfile:
    outfile.write(json_object)
