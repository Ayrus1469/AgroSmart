from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'agromart_secret_key_2024'  # Change this in production

# Global variables for data
df = None

def load_data():
    """Load dataset"""
    global df
    
    try:
        # Load dataset
        if os.path.exists("Fertilizer_Prediction_gpt(1).csv"):
            df = pd.read_csv("Fertilizer_Prediction_gpt(1).csv")
            logger.info(f"Dataset loaded successfully with {len(df)} records")
        else:
            logger.error("Dataset file not found")
            
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")

# Load data on startup
load_data()

@app.route('/')
def index():
    """Main entry point - redirect to login if not authenticated"""
    if session.get('logged_in'):
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'GET':
        if session.get('logged_in'):
            return redirect(url_for('home'))
        return render_template('login.html')
    
    try:
        data = request.form
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # Simple authentication (in production, use proper password hashing)
        if username == "farmer" and password == "12345":
            session['logged_in'] = True
            session['username'] = username
            session['login_time'] = datetime.now().isoformat()
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('home'))
        else:
            error = "Invalid username or password"
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html', error=error)
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return render_template('login.html', error="An error occurred during login")

@app.route('/home')
def home():
    """Home dashboard"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    stats = {
        'total_records': len(df) if df is not None else 0,
        'model_available': False,  # No ML model in simple version
        'dataset_available': df is not None
    }
    
    return render_template('home.html', stats=stats)

@app.route('/recommend')
def recommend():
    """Fertilizer recommendation page"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Get unique values for dropdowns from dataset
    soil_types = []
    crop_types = []
    
    if df is not None:
        soil_types = sorted(df['Soil Type'].unique().tolist())
        crop_types = sorted(df['Crop Type'].unique().tolist())
    
    return render_template('recommendation.html', 
                         soil_types=soil_types, 
                         crop_types=crop_types)

@app.route('/carbon-footprint')
def carbon_footprint():
    """Carbon footprint calculation page"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('carbon_footprint.html')

@app.route('/history')
def history():
    """View recommendation history"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('history.html')

@app.route('/logout')
def logout():
    """Handle user logout"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User {username} logged out")
    return redirect(url_for('login'))

@app.route('/predict', methods=['POST'])
def predict():
    """Get fertilizer recommendation"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['Temperature', 'Humidity', 'Moisture', 'Nitrogen', 
                          'Phosphorus', 'Potassium', 'Soil Type', 'Crop Type']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Convert numeric fields
        try:
            input_row = {
                'Temperature': float(data['Temperature']),
                'Humidity': float(data['Humidity']),
                'Moisture': float(data['Moisture']),
                'Nitrogen': float(data['Nitrogen']),
                'Phosphorus': float(data['Phosphorus']),
                'Potassium': float(data['Potassium']),
                'Soil Type': str(data['Soil Type']),
                'Crop Type': str(data['Crop Type'])
            }
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid numeric value: {str(e)}'}), 400
        
        # Try dataset lookup
        if df is not None:
            recommendation = predict_with_dataset(input_row)
            if recommendation:
                logger.info(f"Dataset lookup successful for user {session.get('username')}")
                return jsonify(recommendation)
        
        # If no exact match, find closest match
        closest_match = find_closest_match(input_row)
        if closest_match:
            logger.info(f"Closest match prediction for user {session.get('username')}")
            return jsonify(closest_match)
        
        return jsonify({'error': 'No suitable fertilizer recommendation found'}), 404
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': 'Internal server error during prediction'}), 500

def predict_with_dataset(input_row):
    """Use dataset lookup for prediction"""
    try:
        # Exact match
        matched = df[
            (df['Temperature'] == input_row['Temperature']) &
            (df['Humidity'] == input_row['Humidity']) &
            (df['Moisture'] == input_row['Moisture']) &
            (df['Nitrogen'] == input_row['Nitrogen']) &
            (df['Phosphorus'] == input_row['Phosphorus']) &
            (df['Potassium'] == input_row['Potassium']) &
            (df['Soil Type'] == input_row['Soil Type']) &
            (df['Crop Type'] == input_row['Crop Type'])
        ]
        
        if not matched.empty:
            fertilizer_name = matched.iloc[0]['Fertilizer Name']
            return {
                'recommendation': fertilizer_name,
                'confidence': 100.0,
                'method': 'Exact Match'
            }
    except Exception as e:
        logger.error(f"Dataset prediction error: {str(e)}")
    
    return None

def find_closest_match(input_row):
    """Find closest match using similarity scoring"""
    try:
        if df is None or df.empty:
            return None
        
        # Filter by soil and crop type first
        filtered_df = df[
            (df['Soil Type'] == input_row['Soil Type']) &
            (df['Crop Type'] == input_row['Crop Type'])
        ]
        
        if filtered_df.empty:
            # If no exact soil/crop match, just filter by crop type
            filtered_df = df[df['Crop Type'] == input_row['Crop Type']]
        
        if filtered_df.empty:
            # If still no match, use all data
            filtered_df = df
        
        # Calculate similarity based on numeric parameters
        numeric_cols = ['Temperature', 'Humidity', 'Moisture', 'Nitrogen', 'Phosphorus', 'Potassium']
        
        scores = []
        for _, row in filtered_df.iterrows():
            score = 0
            for col in numeric_cols:
                # Calculate normalized difference
                diff = abs(row[col] - input_row[col])
                max_val = df[col].max()
                min_val = df[col].min()
                range_val = max_val - min_val if max_val != min_val else 1
                normalized_diff = diff / range_val
                score += (1 - normalized_diff)
            
            scores.append(score / len(numeric_cols))
        
        # Get best match
        best_idx = np.argmax(scores)
        best_match = filtered_df.iloc[best_idx]
        confidence = scores[best_idx] * 100
        
        return {
            'recommendation': best_match['Fertilizer Name'],
            'confidence': min(confidence, 95.0),  # Cap confidence for fuzzy matches
            'method': 'Closest Match'
        }
        
    except Exception as e:
        logger.error(f"Closest match error: {str(e)}")
        return None

@app.route('/api/stats')
def api_stats():
    """Get application statistics"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    stats = {
        'dataset_records': len(df) if df is not None else 0,
        'ml_model_available': False,
        'unique_fertilizers': len(df['Fertilizer Name'].unique()) if df is not None else 0,
        'unique_crops': len(df['Crop Type'].unique()) if df is not None else 0,
        'unique_soil_types': len(df['Soil Type'].unique()) if df is not None else 0
    }
    
    return jsonify(stats)

@app.route('/api/fertilizers')
def api_fertilizers():
    """Get list of all available fertilizers"""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if df is not None:
        fertilizers = sorted(df['Fertilizer Name'].unique().tolist())
        return jsonify(fertilizers)
    
    return jsonify([])

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message="Internal server error"), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    logger.info("Starting AgroSmart application (Simple Version)...")
    app.run(debug=True, host='0.0.0.0', port=5000)