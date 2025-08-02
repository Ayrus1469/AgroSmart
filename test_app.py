from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'test_secret_key'

# Load dataset
try:
    df = pd.read_csv("Fertilizer_Prediction_gpt(1).csv")
    print(f"Dataset loaded: {len(df)} rows")
except Exception as e:
    print(f"Error loading dataset: {e}")
    df = None

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgroSmart Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f8f0; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            input, select, button { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #2e8b57; color: white; cursor: pointer; font-weight: bold; }
            button:hover { background: #246f48; }
            .result { margin-top: 20px; padding: 15px; background: #e8f5e9; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌱 AgroSmart Test</h1>
            <p>Simple fertilizer recommendation system</p>
            
            <form method="POST" action="/login">
                <h3>Login</h3>
                <input type="text" name="username" placeholder="Username (farmer)" required>
                <input type="password" name="password" placeholder="Password (12345)" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'farmer' and password == '12345':
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    # Get soil and crop types from dataset
    soil_types = []
    crop_types = []
    if df is not None:
        soil_types = sorted(df['Soil Type'].unique().tolist())
        crop_types = sorted(df['Crop Type'].unique().tolist())
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AgroSmart Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f0f8f0; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
            input, select, button {{ width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; }}
            button {{ background: #2e8b57; color: white; cursor: pointer; font-weight: bold; grid-column: 1 / -1; }}
            button:hover {{ background: #246f48; }}
            .result {{ margin-top: 20px; padding: 15px; background: #e8f5e9; border-radius: 5px; display: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌱 AgroSmart Dashboard</h1>
            <p>Dataset loaded: {len(df) if df is not None else 0} records</p>
            
            <form id="fertilizerForm" onsubmit="getFertilizerRecommendation(event)">
                <h3>Fertilizer Recommendation</h3>
                <div class="form-grid">
                    <div>
                        <label>Temperature (°C)</label>
                        <input type="number" id="temperature" step="0.1" required placeholder="e.g., 25">
                    </div>
                    <div>
                        <label>Humidity (%)</label>
                        <input type="number" id="humidity" step="0.1" required placeholder="e.g., 65">
                    </div>
                    <div>
                        <label>Moisture (%)</label>
                        <input type="number" id="moisture" step="0.1" required placeholder="e.g., 45">
                    </div>
                    <div>
                        <label>Nitrogen (kg/ha)</label>
                        <input type="number" id="nitrogen" step="0.1" required placeholder="e.g., 120">
                    </div>
                    <div>
                        <label>Phosphorus (kg/ha)</label>
                        <input type="number" id="phosphorus" step="0.1" required placeholder="e.g., 60">
                    </div>
                    <div>
                        <label>Potassium (kg/ha)</label>
                        <input type="number" id="potassium" step="0.1" required placeholder="e.g., 80">
                    </div>
                    <div>
                        <label>Soil Type</label>
                        <select id="soil_type" required>
                            <option value="">Select soil type</option>
                            {''.join([f'<option value="{soil}">{soil}</option>' for soil in soil_types])}
                        </select>
                    </div>
                    <div>
                        <label>Crop Type</label>
                        <select id="crop_type" required>
                            <option value="">Select crop type</option>
                            {''.join([f'<option value="{crop}">{crop}</option>' for crop in crop_types])}
                        </select>
                    </div>
                </div>
                <button type="submit">Get Recommendation</button>
            </form>
            
            <div id="result" class="result">
                <div id="resultContent"></div>
            </div>
            
            <p><a href="/logout">Logout</a></p>
        </div>
        
        <script>
        async function getFertilizerRecommendation(event) {{
            event.preventDefault();
            
            const data = {{
                Temperature: parseFloat(document.getElementById('temperature').value),
                Humidity: parseFloat(document.getElementById('humidity').value),
                Moisture: parseFloat(document.getElementById('moisture').value),
                Nitrogen: parseFloat(document.getElementById('nitrogen').value),
                Phosphorus: parseFloat(document.getElementById('phosphorus').value),
                Potassium: parseFloat(document.getElementById('potassium').value),
                'Soil Type': document.getElementById('soil_type').value,
                'Crop Type': document.getElementById('crop_type').value
            }};
            
            try {{
                const response = await fetch('/predict', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
                
                const result = await response.json();
                const resultDiv = document.getElementById('result');
                const contentDiv = document.getElementById('resultContent');
                
                if (response.ok) {{
                    contentDiv.innerHTML = `
                        <h4>🌿 Recommended Fertilizer</h4>
                        <p><strong>${{result.recommendation}}</strong></p>
                        <p>Confidence: ${{result.confidence.toFixed(1)}}%</p>
                        <p>Method: ${{result.method}}</p>
                    `;
                }} else {{
                    contentDiv.innerHTML = `<p style="color: red;">Error: ${{result.error}}</p>`;
                }}
                
                resultDiv.style.display = 'block';
            }} catch (error) {{
                console.error('Error:', error);
                document.getElementById('resultContent').innerHTML = `<p style="color: red;">Connection error</p>`;
                document.getElementById('result').style.display = 'block';
            }}
        }}
        </script>
    </body>
    </html>
    '''

@app.route('/predict', methods=['POST'])
def predict():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        if df is None:
            return jsonify({'error': 'Dataset not available'}), 500
        
        # Try exact match first
        matched = df[
            (df['Temperature'] == data['Temperature']) &
            (df['Humidity'] == data['Humidity']) &
            (df['Moisture'] == data['Moisture']) &
            (df['Nitrogen'] == data['Nitrogen']) &
            (df['Phosphorus'] == data['Phosphorus']) &
            (df['Potassium'] == data['Potassium']) &
            (df['Soil Type'] == data['Soil Type']) &
            (df['Crop Type'] == data['Crop Type'])
        ]
        
        if not matched.empty:
            fertilizer_name = matched.iloc[0]['Fertilizer Name']
            return jsonify({
                'recommendation': fertilizer_name,
                'confidence': 100.0,
                'method': 'Exact Match'
            })
        
        # If no exact match, find closest by crop and soil type
        filtered = df[
            (df['Soil Type'] == data['Soil Type']) &
            (df['Crop Type'] == data['Crop Type'])
        ]
        
        if not filtered.empty:
            # Just take the first match for simplicity
            fertilizer_name = filtered.iloc[0]['Fertilizer Name']
            return jsonify({
                'recommendation': fertilizer_name,
                'confidence': 85.0,
                'method': 'Soil & Crop Match'
            })
        
        # Last resort - match by crop only
        crop_match = df[df['Crop Type'] == data['Crop Type']]
        if not crop_match.empty:
            fertilizer_name = crop_match.iloc[0]['Fertilizer Name']
            return jsonify({
                'recommendation': fertilizer_name,
                'confidence': 70.0,
                'method': 'Crop Match Only'
            })
        
        return jsonify({'error': 'No recommendation found'}), 404
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("Starting AgroSmart Test Application...")
    print("Go to: http://localhost:5000")
    print("Login: farmer / 12345")
    app.run(debug=True, host='0.0.0.0', port=5000)