
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import csv
import pandas as pd
from difflib import SequenceMatcher
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# -------------------- LOGIN FUNCTIONALITY --------------------

def check_credentials(email, password):
    try:
        with open('enter.csv', mode='r', newline='', encoding='latin1') as csvfile:
            reader = csv.DictReader(csvfile)
            print("CSV Headers detected:", reader.fieldnames)
            for row in reader:
                print("Row keys:", list(row.keys()))
                if row.get('email') == email and row.get('password') == password:
                    return True
        return False
    except FileNotFoundError:
        print("ERROR: 'enter.csv' not found.")
        return False
    except Exception as e:
        print("Unexpected error while reading CSV:", e)
        return False

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    print("Login route called. Request method:", request.method)
    if request.method == 'OPTIONS':
        return ('', 200)

    data = request.get_json()
    if data is None:
        return jsonify({'success': False, 'error': 'No JSON data received'}), 400

    print("Received JSON data:", data)
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'}), 400

    if check_credentials(email, password):
        print(f"Login successful for user: {email}")
        return jsonify({'success': True})
    else:
        print(f"Login failed for user: {email}")
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

# -------------------- ANALYSIS FUNCTIONALITY --------------------

CSV_FILE_PATH = r"C:\Users\Hamid\Desktop\project\mammo\my new file for analyze.csv"

try:
    data = pd.read_csv(CSV_FILE_PATH)
except Exception as e:
    print("Error loading analysis CSV file:", e)
    data = pd.DataFrame()

def calculate_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

@app.route('/analyze', methods=['POST'])
def analyze_message():
    try:
        print("Request received:", request.json)

        message_content = request.json.get('message')
        uploaded_file_name = request.json.get('file_name', 'Unknown_Image')  
        mask_position = request.json.get('mask_position', 'Unspecified Area')

        if not message_content:
            return jsonify({'error': 'Message content is missing'}), 400

        if data.empty or 'message' not in data.columns or 'image name' not in data.columns:
            return jsonify({'error': 'CSV file is empty or missing required columns'}), 500

        threshold = 0.96    
        results = []
        
        for _, row in data.iterrows():
            similarity = calculate_similarity(message_content, row['message'])
            if similarity >= threshold:
                results.append({
                    'image_name': row['image name'],
                    'message': row['message'],
                    'similarity': round(similarity * 100, 2)
                })

        results.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = results[:5]

        file_content = f"Patient Name: {uploaded_file_name}\n\n"
        file_content += "Mammography interpertation:\n"
        for result in top_results:
            file_content += f"In this image: {result['image_name']} has been seen.\n"
            file_content += f"Detected a hyperdense area in {mask_position} of mammography image.\n"
            file_content += "No/An asymmetry has been detected.\n"
            file_content += "No/An increasing size of breast skin has been detected.\n\n"

        file_path = "analysis_results.txt"
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(file_content)

        return send_file(file_path, as_attachment=True, download_name="analysis_results.txt", mimetype="text/plain")

    except Exception as e:
        print("Error during analysis:", str(e))
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True)
