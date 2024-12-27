import requests
from flask import Flask, request, jsonify, render_template
from geopy.distance import geodesic
import json

app = Flask(__name__)

# API keys (replace with your actual API keys)
TOMTOM_API_KEY = "xTLfTJNbicn6vhY5J6nARS3GIb09kPpU"
GOOGLE_MAPS_API_KEY = "AIzaSyDJihk0DU14ug7oTvgaxKLsvwMPR5YG0TY"
AQICN_API_KEY = "ce598bd91871b3c14157ad55645e3618ea8dad02"
OSRM_BASE_URL = "http://router.project-osrm.org"  # Replace with your OSRM server URL if needed
OSRM_API_KEY = None  # Replace with your API key if required

# Simplified emissions factors (g CO2 per km)
EMISSIONS_FACTORS = {
    "small_van": 147,
    "large_van": 252,
    "truck": 887
}

def get_traffic_data(start, end):
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{start[0]},{start[1]}:{end[0]},{end[1]}/json"
    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["routes"][0]["summary"]["trafficDelayInSeconds"]

def get_weather_data(lat, lon):
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQICN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data["data"]["aqi"]

def get_route(start, end):
    url = f"{OSRM_BASE_URL}/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
    params = {
        "overview": "full",
        "geometries": "geojson"
    }
    if OSRM_API_KEY:
        params["api_key"] = OSRM_API_KEY
    response = requests.get(url, params=params)
    data = response.json()
    return data["routes"][0]["geometry"]["coordinates"]

def calculate_emissions(distance, vehicle_type):
    return (distance / 1000) * EMISSIONS_FACTORS[vehicle_type]

def optimize_route(start, end, vehicle_type):
    traffic_delay = get_traffic_data(start, end)
    weather_condition = get_weather_data(start[0], start[1])
    route = get_route(start, end)
    
    distance = sum(geodesic(route[i], route[i+1]).km for i in range(len(route)-1))
    emissions = calculate_emissions(distance, vehicle_type)
    
    return {
        "route": route,
        "distance": distance,
        "traffic_delay": traffic_delay,
        "weather_condition": weather_condition,
        "emissions": emissions
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.json
    start = (data['start_lat'], data['start_lon'])
    end = (data['end_lat'], data['end_lon'])
    vehicle_type = data['vehicle_type']
    
    result = optimize_route(start, end, vehicle_type)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)

