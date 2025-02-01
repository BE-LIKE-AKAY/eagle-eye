from flask import Flask, request, render_template, jsonify
import os
import json
import datetime
import requests

app = Flask(__name__)
DATA_FOLDER = "data"  # Folder containing text files
LOG_FILE = "search_log.json"

# Function to get user details
def get_user_details(request):
    ip = request.remote_addr
    screen_res = request.headers.get("Screen-Resolution", "Unknown")
    cookies = request.cookies.to_dict()
    
    # Get location details
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        location_data = response.json()
    except:
        location_data = {}
    
    return {
        "ip": ip,
        "screen_resolution": screen_res,
        "location": location_data.get("city", "Unknown") + ", " + location_data.get("region", "Unknown"),
        "isp": location_data.get("org", "Unknown"),
        "network_type": "Unknown",  # Requires frontend detection
        "connection_speed": "Unknown",  # Requires frontend detection
        "cookies": cookies
    }

# Function to search keyword in files
def search_files(keyword):
    results = []
    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith(".txt"):
            filepath = os.path.join(DATA_FOLDER, filename)
            with open(filepath, "r", encoding="utf-8") as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    if keyword.lower() in line.lower():
                        results.append({"file": filename, "line": i+1, "content": line.strip()})
    return results

# Function to log search activity
def log_search(user_data, keyword):
    log_entry = {
        **user_data,
        "keyword": keyword,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as log_file:
            logs = json.load(log_file)
    else:
        logs = []
    
    logs.append(log_entry)
    
    with open(LOG_FILE, "w", encoding="utf-8") as log_file:
        json.dump(logs, log_file, indent=4)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get("keyword")
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400
    
    user_data = get_user_details(request)
    results = search_files(keyword)
    log_search(user_data, keyword)
    
    return jsonify({"results": results})

if __name__ == '__main__':
    os.makedirs(DATA_FOLDER, exist_ok=True)
    app.run(debug=True, host="0.0.0.0")
