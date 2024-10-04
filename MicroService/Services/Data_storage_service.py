from flask import Flask, request, jsonify
from influxdb import InfluxDBClient
import json

app = Flask(__name__)

# Configure InfluxDB
INFLUXDB_ADDRESS = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_USER = 'your_user'
INFLUXDB_PASSWORD = 'your_password'
INFLUXDB_DATABASE = 'emg_data'

client = InfluxDBClient(INFLUXDB_ADDRESS, INFLUXDB_PORT, INFLUXDB_USER, INFLUXDB_PASSWORD, INFLUXDB_DATABASE)

# Create database if it doesn't exist
client.create_database(INFLUXDB_DATABASE)

def write_to_influxdb(measurement, data):
    json_body = [
        {
            "measurement": measurement,
            "fields": data
        }
    ]
    client.write_points(json_body)

@app.route('/store_raw', methods=['POST'])
def store_raw_data():
    data = request.get_json()
    write_to_influxdb('raw_emg_data', data)
    return jsonify({"status": "raw data stored"}), 200

@app.route('/store_features', methods=['POST'])
def store_features():
    data = request.get_json()
    write_to_influxdb('extracted_features', data)
    return jsonify({"status": "features stored"}), 200

@app.route('/store_normalized', methods=['POST'])
def store_normalized_data():
    data = request.get_json()
    write_to_influxdb('normalized_data', data)
    return jsonify({"status": "normalized data stored"}), 200

@app.route('/store_predictions', methods=['POST'])
def store_predictions():
    data = request.get_json()
    write_to_influxdb('predictions', data)
    return jsonify({"status": "predictions stored"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
