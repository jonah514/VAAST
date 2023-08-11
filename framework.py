from io import BytesIO
import pandas as pd
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from filter import Filter
from analysis_files.disappearing_signal import iterate_df
from analysis_files.patrolling_behavior import handler
from worldgraph import WorldGraph
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS, cross_origin
import ast
import aws_files.data_files.aws_session as aws

#disables warning for no verify ssl
import urllib3
urllib3.disable_warnings()

app = Flask(__name__, static_url_path = '/static')
CORS(app, support_credentials=True)

dynamodb = boto3.resource('dynamodb', 
    region_name = 'us-gov-east-1',
    verify = False)

#initializing dynamodb tables
flights = dynamodb.Table('fr24_timestamp')
ships = dynamodb.Table('intelliearth_timestamp')
plane_paths = dynamodb.Table('plane_paths')
ship_paths = dynamodb.Table('ship_paths')

global_flight_df = pd.DataFrame()
global_ship_df = pd.DataFrame()

#hardcoded timestamp for demo. Is updated when new timestamps are searched for
timestamp = '2023-05-15 17:47:10'

#state of filters for keeping html updated and using filters
show_ships = True
show_planes = True
show_commercial = True
show_military = True
show_international = True
show_domestic = True
altitude_range = [0, 100000]
speed_range = [0, 2000]

# Slower version
# graph = WorldGraph('static/Graph1distEnhanced.txt', 1, 1)
# Faster version
graph = WorldGraph('static/Graph1distEnhanced.txt', 1, 1)

#default endpoint, loads html file
@app.route('/')
def index():
    global timestamp
    return send_file('index.html')

#performs disappearing signal or patrolling analysis, receives ajax string for type of analysis to perform.
@app.route('/analysis', methods = ['GET', 'POST'])
def performAnalysis():
    global global_flight_df
    typeOfAnalysis = request.form["type"]
    if (typeOfAnalysis == "disappearing"):
        returnDF = iterate_df(global_flight_df)
        returnDF = returnDF.to_json(orient = 'records')
        return jsonify(returnDF)
    elif (typeOfAnalysis == "patrolling"):
        returnDF = handler(global_flight_df).to_json(orient = 'records')
        return jsonify(returnDF)
    else:
        return "Error, Analysis not valid"

#returns status of filters to update html boxes
@app.route('/filterstatus')
def returnFilterStatus():
    global show_ships, show_planes, show_commercial, show_military, show_international, show_domestic, altitude_range, speed_range
    return [show_ships, show_planes, show_commercial, show_military, show_international, show_domestic, altitude_range, speed_range]

#gets flight data from dynamodb
@app.route('/flightdata')
@cross_origin(supports_credentials=True)
def get_flight_data():
    global global_flight_df, timestamp, show_planes, show_commercial, show_military, show_international, show_domestic, altitude_range, speed_range
    print(type(show_planes), show_ships, show_commercial, show_military, show_international, show_domestic, type(altitude_range), speed_range)
    if show_planes == "false":
        return jsonify(pd.DataFrame().to_json(orient = 'records'))
    else:
        filter = Filter(show_domestic, show_international, show_military, show_commercial, altitude_range, speed_range) #dom : bool, inter : bool, mil : bool, commercial : bool, alt : tuple, speed : tuple
        date = timestamp[0:10]
        time = timestamp[11:]
        flight_response = flights.query(
            KeyConditionExpression=Key('Date').eq(date) & Key('Time_ID').begins_with(time)
        )
        global_flight_df = pd.DataFrame(flight_response['Items'])

        filtered_flight_df = filter.plane_apply_filter(global_flight_df)

        flight_df_json = filtered_flight_df.to_json(orient = 'records')
        return jsonify(flight_df_json)
#same for ships
@app.route('/shipdata')
@cross_origin(supports_credentials=True)
def get_ship_data():
    global global_ship_df, timestamp, show_ships, speed_range
    if show_ships == "false":
        return jsonify(pd.DataFrame().to_json(orient = 'records'))
    else:
        filter = Filter(True, True, True, True, [0, 100000], speed_range)
        date = timestamp[0:10]

        time = timestamp[11:]
        #print(f"Time: {time}")
        time = f"{str(int(time[:2])+6)}{time[2:]}"

        ship_response = ships.query(
            KeyConditionExpression=Key('Date').eq('2023-05-16') & Key('Time_ID').begins_with(time)
        )

        global_ship_df = pd.DataFrame(ship_response['Items'])
        #print(global_ship_df)
        filtered_ship_df = filter.ship_apply_filter(global_ship_df)
        ship_df_json = filtered_ship_df.to_json(orient = 'records')
        return jsonify(ship_df_json)

#updates timestamp global variable and reloads index
@app.route('/newtimestamp', methods=['POST'])
def handle_request():
    global timestamp
    timestamp = request.form.get("textInput")
    return send_file('index.html')

#calculates prediction using shortest paths
@app.route('/prediction', methods=['POST', 'GET'])
def display_prediction():
    global graph
    origin = request.form['origin_airport']
    destination = request.form['dest_airport']
    print(destination)
    predicted_path = graph.predict_trajectory(origin, destination)
    print(predicted_path)
    return predicted_path#jsonify(predicted_path)

#gets filter values from html and updates the global variables (filtering is not performed until flightdata endpoint is routed)
@app.route('/filter', methods=['POST', 'GET'])
def apply_filter():
    global show_planes, show_ships, show_commercial, show_military, show_international, show_domestic, altitude_range, speed_range

    show_planes = request.form["planes"]
    show_ships = request.form["ships"]
    show_commercial = request.form["com"]
    show_military = request.form["mil"]
    show_international = request.form["int"]
    show_domestic = request.form["dom"]
    altitude_range = [float(request.form["altmin"]), float(request.form["altmax"])]
    speed_range = [float(request.form["speedmin"]), float(request.form["speedmax"])]

    print(show_planes, show_ships, show_commercial, show_military, show_international, show_domestic, altitude_range, speed_range)
    return ""

#request path data from dynamodb
@app.route('/getplanepath', methods=['POST', 'GET'])
def request_plane_path():
    global timestamp

    requested_ID = request.form['javascript_data']

    path_response = plane_paths.query(
        KeyConditionExpression=Key('ID').eq(requested_ID)
    )
    path_df = pd.DataFrame(path_response['Items'])
    path_json = path_df.to_json(orient = 'records')
    return jsonify(path_json)

#request path data from dynamodb
@app.route('/getshippath', methods=['POST', 'GET'])
def request_ship_path():
    global timestamp

    requested_ID = request.form['javascript_data']

    path_response = ship_paths.query(
        KeyConditionExpression=Key('ID').eq(requested_ID)
    )
    path_df = pd.DataFrame(path_response['Items'])
    path_json = path_df.to_json(orient = 'records')
    return jsonify(path_json)


if __name__ == '__main__':
    app.run()