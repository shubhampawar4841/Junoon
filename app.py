from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)

# Load the data
df = pd.read_csv('funeral_services_data.csv')

# Function to handle NaN values in JSON serialization
def handle_nan(obj):
    if pd.isna(obj):
        return None
    return obj

@app.route('/api/data')
def get_data():
    # Convert DataFrame to dict and handle NaN values
    data = df.replace({np.nan: None}).to_dict('records')
    return jsonify({'data': data})

@app.route('/api/stats')
def get_stats():
    # Calculate statistics and handle NaN values
    stats = {}
    
    # Type distribution
    if 'Type' in df.columns:
        stats['typeDistribution'] = df['Type'].value_counts().replace({np.nan: None}).to_dict()
    else:
        stats['typeDistribution'] = {}
    
    # State distribution (extract from address if available)
    if 'Address' in df.columns:
        # Extract state from address (assuming US addresses)
        df['State'] = df['Address'].str.extract(r',\s*([A-Z]{2})\s*\d*$')
        stats['stateDistribution'] = df['State'].value_counts().replace({np.nan: None}).to_dict()
    else:
        stats['stateDistribution'] = {}
    
    return jsonify(stats)

@app.route('/api/search')
def search():
    query = request.args.get('q', '').lower()
    if not query:
        data = df.replace({np.nan: None}).to_dict('records')
        return jsonify({'data': data})
    
    filtered_df = df[
        df['Business Name'].str.lower().str.contains(query) |
        df['Type'].str.lower().str.contains(query) |
        df['Address'].str.lower().str.contains(query)
    ]
    
    data = filtered_df.replace({np.nan: None}).to_dict('records')
    return jsonify({'data': data})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 