from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import pandas as pd
import numpy as np
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'agromart_secret_key_2024'

# Load dataset
try:
    df = pd.read_csv("Fertilizer_Prediction_gpt(1).csv")
    logger.info(f"Dataset loaded: {len(df)} rows")
except Exception as e:
    logger.error(f"Error loading dataset: {e}")
    df = None

# HTML templates as strings to avoid template file issues
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AgroSmart - Login</title>
    <style>
        :root {
            --primary: #2e8b57;
            --primary-dark: #246f48;
            --bg: linear-gradient(135deg, #f5fff5 0%, #e8f5e9 100%);
            --card-bg: rgba(255, 255, 255, 0.95);
            --shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            --error: #f44336;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', 'Arial', sans-serif;
            background: var(--bg);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-card {
            background: var(--card-bg);
            padding: 3rem;
            border-radius: 20px;
            box-shadow: var(--shadow);
            width: 100%;
            max-width: 400px;
            backdrop-filter: blur(10px);
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .login-header h1 {
            color: var(--primary);
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .login-header p {
            color: #666;
            font-size: 1rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #333;
        }
        
        .form-group input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(46, 139, 87, 0.1);
        }
        
        .submit-btn {
            width: 100%;
            padding: 1rem 2rem;
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(46, 139, 87, 0.3);
        }
        
        .error-text {
            color: var(--error);
            margin-top: 1rem;
            font-size: 1rem;
            font-weight: 500;
            padding: 1rem;
            background: rgba(244, 67, 54, 0.1);
            border-radius: 8px;
            border-left: 4px solid var(--error);
        }
        
        .login-info {
            margin-top: 2rem;
            padding: 1.5rem;
            background: rgba(46, 139, 87, 0.05);
            border-radius: 12px;
            border-left: 4px solid var(--primary);
        }
        
        .login-info h3 {
            color: var(--primary);
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <div class="login-header">
            <h1>🌱 AgroSmart</h1>
            <p>Smart Agricultural Solutions</p>
        </div>
        
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required placeholder="Enter username">
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required placeholder="Enter password">
            </div>
            
            {% if error %}
            <div class="error-text">{{ error }}</div>
            {% endif %}
            
            <button type="submit" class="submit-btn">Sign In</button>
        </form>
        
        <div class="login-info">
            <h3>Demo Credentials</h3>
            <p><strong>Username:</strong> farmer</p>
            <p><strong>Password:</strong> 12345</p>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AgroSmart - Dashboard</title>
    <style>
        :root {
            --primary: #2e8b57;
            --primary-dark: #246f48;
            --primary-light: #e8f5e9;
            --secondary: #ffa726;
            --bg: linear-gradient(135deg, #f5fff5 0%, #e8f5e9 100%);
            --card-bg: rgba(255, 255, 255, 0.95);
            --shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            --shadow-hover: 0 12px 35px rgba(0, 0, 0, 0.15);
            --success: #4caf50;
            --error: #f44336;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', 'Arial', sans-serif;
            background: var(--bg);
            color: #333;
            line-height: 1.6;
            min-height: 100vh;
        }
        
        .navbar {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            padding: 1rem 2rem;
            color: white;
            box-shadow: var(--shadow);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .navbar-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 1.8rem;
            font-weight: 700;
            letter-spacing: 0.5px;
        }
        
        .nav-links {
            display: flex;
            gap: 1rem;
            list-style: none;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            padding: 0.75rem 1.25rem;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        
        .nav-links a:hover {
            background-color: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
        }
        
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        
        .hero {
            text-align: center;
            padding: 4rem 2rem;
            background: var(--card-bg);
            border-radius: 20px;
            box-shadow: var(--shadow);
            margin-bottom: 3rem;
        }
        
        .hero h1 {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }
        
        .card {
            background: var(--card-bg);
            border-radius: 20px;
            padding: 3rem;
            box-shadow: var(--shadow);
            margin-bottom: 2rem;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-hover);
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
        }
        
        .form-group label {
            font-weight: 600;
            margin-bottom: 0.75rem;
            color: #333;
            font-size: 1rem;
        }
        
        .form-group input,
        .form-group select {
            padding: 1rem 1.25rem;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: white;
        }
        
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 4px rgba(46, 139, 87, 0.1);
        }
        
        .submit-btn {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 15px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 1.5rem;
        }
        
        .submit-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(46, 139, 87, 0.3);
        }
        
        .result {
            background: linear-gradient(135deg, var(--primary-light), rgba(129, 199, 132, 0.1));
            border-radius: 15px;
            padding: 2rem;
            margin-top: 2rem;
            border-left: 5px solid var(--primary);
            display: none;
        }
        
        .result.show {
            display: block;
            animation: fadeInUp 0.5s ease;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .error-text {
            color: var(--error);
            background: rgba(244, 67, 54, 0.1);
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid var(--error);
        }
        
        @media (max-width: 768px) {
            .hero h1 { font-size: 2rem; }
            .form-grid { grid-template-columns: 1fr; }
            .card { padding: 2rem 1.5rem; }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <div class="logo">🌱 AgroSmart</div>
            <ul class="nav-links">
                <li><a href="/dashboard">Dashboard</a></li>
                <li><a href="/logout">Logout</a></li>
            </ul>
        </div>
    </nav>

    <main class="container">
        <div class="hero">
            <h1>Welcome to AgroSmart</h1>
            <p>Your intelligent partner for sustainable agriculture. Get data-driven fertilizer recommendations using advanced algorithms.</p>
        </div>

        <div class="card">
            <h2>📊 System Status</h2>
            <p><strong>Dataset Records:</strong> {{ dataset_count }} fertilizer combinations</p>
            <p><strong>System Status:</strong> ✅ Online and Ready</p>
        </div>

        <div class="card">
            <h2>🌿 Fertilizer Recommendation</h2>
            <p>Enter your soil and crop details below to get personalized fertilizer recommendations.</p>

            <form id="fertilizerForm" onsubmit="getFertilizerRecommendation(event)">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="temperature">🌡️ Temperature (°C)</label>
                        <input type="number" id="temperature" step="0.1" required placeholder="e.g., 25.5">
                    </div>

                    <div class="form-group">
                        <label for="humidity">💧 Humidity (%)</label>
                        <input type="number" id="humidity" step="0.1" required placeholder="e.g., 65.0">
                    </div>

                    <div class="form-group">
                        <label for="moisture">🌊 Soil Moisture (%)</label>
                        <input type="number" id="moisture" step="0.1" required placeholder="e.g., 45.0">
                    </div>

                    <div class="form-group">
                        <label for="nitrogen">🧪 Nitrogen (kg/ha)</label>
                        <input type="number" id="nitrogen" step="0.1" required placeholder="e.g., 120.0">
                    </div>

                    <div class="form-group">
                        <label for="phosphorus">⚗️ Phosphorus (kg/ha)</label>
                        <input type="number" id="phosphorus" step="0.1" required placeholder="e.g., 60.0">
                    </div>

                    <div class="form-group">
                        <label for="potassium">🧲 Potassium (kg/ha)</label>
                        <input type="number" id="potassium" step="0.1" required placeholder="e.g., 80.0">
                    </div>

                    <div class="form-group">
                        <label for="soil_type">🌍 Soil Type</label>
                        <select id="soil_type" required>
                            <option value="">Select soil type</option>
                            {% for soil_type in soil_types %}
                            <option value="{{ soil_type }}">{{ soil_type }}</option>
                            {% endfor %}
                        </select>
                    </div>

                    <div class="form-group">
                        <label for="crop_type">🌾 Crop Type</label>
                        <select id="crop_type" required>
                            <option value="">Select crop type</option>
                            {% for crop_type in crop_types %}
                            <option value="{{ crop_type }}">{{ crop_type }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>

                <button type="submit" class="submit-btn">Get Recommendation</button>
            </form>

            <div id="result" class="result">
                <div id="resultContent"></div>
            </div>
        </div>

        <div class="card">
            <h3>💡 Tips for Better Recommendations</h3>
            <ul style="padding-left: 1.5rem; line-height: 1.8;">
                <li><strong>Soil Testing:</strong> Use recent soil test results for accurate NPK values</li>
                <li><strong>Weather Data:</strong> Enter current or expected weather conditions</li>
                <li><strong>Crop Stage:</strong> Consider your crop's growth stage for timing</li>
                <li><strong>Local Conditions:</strong> Factor in your region's typical growing conditions</li>
            </ul>
        </div>
    </main>

    <script>
    async function getFertilizerRecommendation(event) {
        event.preventDefault();
        
        const submitBtn = document.querySelector('.submit-btn');
        const resultDiv = document.getElementById('result');
        const contentDiv = document.getElementById('resultContent');
        
        // Show loading state
        submitBtn.textContent = 'Analyzing...';
        submitBtn.disabled = true;
        
        const data = {
            Temperature: parseFloat(document.getElementById('temperature').value),
            Humidity: parseFloat(document.getElementById('humidity').value),
            Moisture: parseFloat(document.getElementById('moisture').value),
            Nitrogen: parseFloat(document.getElementById('nitrogen').value),
            Phosphorus: parseFloat(document.getElementById('phosphorus').value),
            Potassium: parseFloat(document.getElementById('potassium').value),
            'Soil Type': document.getElementById('soil_type').value,
            'Crop Type': document.getElementById('crop_type').value
        };
        
        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                contentDiv.innerHTML = `
                    <h4>🌿 Recommended Fertilizer</h4>
                    <p style="font-size: 1.3rem; font-weight: bold; color: var(--primary); margin: 1rem 0;">
                        ${result.recommendation}
                    </p>
                    <p><strong>Confidence:</strong> ${result.confidence.toFixed(1)}%</p>
                    <p><strong>Method:</strong> ${result.method}</p>
                    <div style="margin-top: 1rem; padding: 1rem; background: rgba(46, 139, 87, 0.1); border-radius: 8px;">
                        <p><strong>Input Summary:</strong></p>
                        <p>Crop: ${data['Crop Type']} on ${data['Soil Type']} soil</p>
                        <p>NPK: ${data.Nitrogen}:${data.Phosphorus}:${data.Potassium}</p>
                        <p>Conditions: ${data.Temperature}°C, ${data.Humidity}% humidity</p>
                    </div>
                `;
                resultDiv.className = 'result show';
            } else {
                contentDiv.innerHTML = `<div class="error-text">Error: ${result.error}</div>`;
                resultDiv.className = 'result show';
            }
            
        } catch (error) {
            console.error('Error:', error);
            contentDiv.innerHTML = `<div class="error-text">Connection error. Please try again.</div>`;
            resultDiv.className = 'result show';
        } finally {
            submitBtn.textContent = 'Get Recommendation';
            submitBtn.disabled = false;
        }
    }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if username == 'farmer' and password == '12345':
        session['logged_in'] = True
        session['username'] = username
        logger.info(f"User {username} logged in successfully")
        return redirect(url_for('dashboard'))
    else:
        error = "Invalid username or password"
        logger.warning(f"Failed login attempt for username: {username}")
        return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    # Get unique values for dropdowns from dataset
    soil_types = []
    crop_types = []
    dataset_count = 0
    
    if df is not None:
        soil_types = sorted(df['Soil Type'].unique().tolist())
        crop_types = sorted(df['Crop Type'].unique().tolist())
        dataset_count = len(df)
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        soil_types=soil_types,
        crop_types=crop_types,
        dataset_count=dataset_count
    )

@app.route('/predict', methods=['POST'])
def predict():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        if df is None:
            return jsonify({'error': 'Dataset not available'}), 500
        
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
        
        # Try exact match first
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
            logger.info(f"Exact match found for user {session.get('username')}")
            return jsonify({
                'recommendation': fertilizer_name,
                'confidence': 100.0,
                'method': 'Exact Match'
            })
        
        # Find closest match using similarity scoring
        numeric_cols = ['Temperature', 'Humidity', 'Moisture', 'Nitrogen', 'Phosphorus', 'Potassium']
        
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
        
        # Calculate similarity scores
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
        
        logger.info(f"Closest match found for user {session.get('username')}")
        return jsonify({
            'recommendation': best_match['Fertilizer Name'],
            'confidence': min(confidence, 95.0),  # Cap confidence for fuzzy matches
            'method': 'Similarity Match'
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({'error': 'Internal server error during prediction'}), 500

@app.route('/logout')
def logout():
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User {username} logged out")
    return redirect(url_for('index'))

if __name__ == '__main__':
    logger.info("Starting AgroSmart Application...")
    logger.info("Access at: http://localhost:5000")
    logger.info("Login: farmer / 12345")
    app.run(debug=True, host='0.0.0.0', port=5001)