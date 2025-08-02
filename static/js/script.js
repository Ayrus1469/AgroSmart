// Enhanced AgroSmart Frontend JavaScript
class AgroSmart {
    constructor() {
        this.recommendations = JSON.parse(localStorage.getItem('agrosmartHistory') || '[]');
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupEventListeners();
            this.setupFormValidation();
            this.loadHistory();
        });
    }

    setupEventListeners() {
        // Login form handler
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Fertilizer recommendation form handler
        const fertilizerForm = document.getElementById('fertilizerForm');
        if (fertilizerForm) {
            fertilizerForm.addEventListener('submit', (e) => this.handleFertilizerRecommendation(e));
        }

        // Carbon footprint form handler
        const carbonForm = document.getElementById('carbonForm');
        if (carbonForm) {
            carbonForm.addEventListener('submit', (e) => this.handleCarbonFootprint(e));
        }

        // Clear history button
        const clearHistoryBtn = document.getElementById('clearHistory');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        }

        // Export data button
        const exportBtn = document.getElementById('exportData');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportData());
        }
    }

    setupFormValidation() {
        const inputs = document.querySelectorAll('input[type="number"]');
        inputs.forEach(input => {
            input.addEventListener('input', (e) => this.validateNumberInput(e));
            input.addEventListener('blur', (e) => this.validateRange(e));
        });
    }

    validateNumberInput(event) {
        const input = event.target;
        const value = parseFloat(input.value);
        
        // Remove any non-numeric characters except decimal point
        input.value = input.value.replace(/[^\d.-]/g, '');
        
        // Add visual feedback
        if (input.value && !isNaN(value) && value >= 0) {
            input.classList.add('valid');
            input.classList.remove('invalid');
        } else if (input.value) {
            input.classList.add('invalid');
            input.classList.remove('valid');
        } else {
            input.classList.remove('valid', 'invalid');
        }
    }

    validateRange(event) {
        const input = event.target;
        const value = parseFloat(input.value);
        const fieldName = input.id;
        
        // Define realistic ranges for different parameters
        const ranges = {
            'Temperature': { min: -10, max: 50, unit: '°C' },
            'Humidity': { min: 0, max: 100, unit: '%' },
            'Moisture': { min: 0, max: 100, unit: '%' },
            'Nitrogen': { min: 0, max: 500, unit: 'kg/ha' },
            'Phosphorus': { min: 0, max: 200, unit: 'kg/ha' },
            'Potassium': { min: 0, max: 300, unit: 'kg/ha' }
        };

        if (ranges[fieldName] && value !== '' && !isNaN(value)) {
            const range = ranges[fieldName];
            if (value < range.min || value > range.max) {
                this.showTooltip(input, `Value should be between ${range.min} and ${range.max} ${range.unit}`);
                input.classList.add('warning');
            } else {
                input.classList.remove('warning');
                this.hideTooltip(input);
            }
        }
    }

    showTooltip(element, message) {
        this.hideTooltip(element); // Remove existing tooltip
        
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = message;
        tooltip.style.cssText = `
            position: absolute;
            background: var(--warning);
            color: white;
            padding: 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            max-width: 200px;
        `;
        
        element.parentNode.appendChild(tooltip);
        element.setAttribute('data-has-tooltip', 'true');
        
        // Position tooltip
        const rect = element.getBoundingClientRect();
        const parentRect = element.parentNode.getBoundingClientRect();
        tooltip.style.top = (rect.bottom - parentRect.top + 5) + 'px';
        tooltip.style.left = (rect.left - parentRect.left) + 'px';
    }

    hideTooltip(element) {
        if (element.getAttribute('data-has-tooltip')) {
            const tooltip = element.parentNode.querySelector('.tooltip');
            if (tooltip) {
                tooltip.remove();
            }
            element.removeAttribute('data-has-tooltip');
        }
    }

    async handleLogin(event) {
        event.preventDefault();
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();
        const submitBtn = event.target.querySelector('.submit-btn');
        const errorDiv = document.getElementById('loginError');

        // Add loading state
        this.setButtonLoading(submitBtn, true);
        
        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
            });

            if (response.redirected) {
                window.location.href = response.url;
            } else {
                const text = await response.text();
                if (text.includes('Invalid')) {
                    this.showError(errorDiv, 'Invalid username or password');
                }
            }
        } catch (error) {
            this.showError(errorDiv, 'Connection error. Please try again.');
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    }

    async handleFertilizerRecommendation(event) {
        event.preventDefault();
        
        const formData = this.getFormData(event.target);
        const resultBox = document.getElementById('result');
        const submitBtn = event.target.querySelector('.submit-btn');

        // Validate all required fields
        if (!this.validateForm(event.target)) {
            this.showError(resultBox, 'Please fill in all required fields with valid values.');
            return;
        }

        this.setButtonLoading(submitBtn, true);
        this.showResult(resultBox, 'Analyzing soil parameters and generating recommendation...', 'loading');

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Prediction failed');
            }

            if (result.recommendation) {
                const recommendation = {
                    id: Date.now(),
                    timestamp: new Date().toISOString(),
                    inputs: formData,
                    fertilizer: result.recommendation,
                    confidence: result.confidence || 100
                };

                this.saveRecommendation(recommendation);
                this.displayRecommendation(resultBox, recommendation);
                this.updateHistory();
            } else {
                throw new Error(result.error || 'No recommendation available');
            }
        } catch (error) {
            this.showError(resultBox, error.message);
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    }

    async handleCarbonFootprint(event) {
        event.preventDefault();
        
        const formData = this.getFormData(event.target);
        const resultBox = document.getElementById('carbonResult');
        const submitBtn = event.target.querySelector('.submit-btn');

        this.setButtonLoading(submitBtn, true);
        this.showResult(resultBox, 'Calculating carbon footprint...', 'loading');

        try {
            // Calculate carbon footprint based on fertilizer usage
            const carbonData = this.calculateCarbonFootprint(formData);
            this.displayCarbonFootprint(resultBox, carbonData);
        } catch (error) {
            this.showError(resultBox, error.message);
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    }

    getFormData(form) {
        const formData = {};
        const inputs = form.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            if (input.type === 'number') {
                formData[input.id] = parseFloat(input.value) || 0;
            } else {
                formData[input.id] = input.value;
            }
        });
        
        return formData;
    }

    validateForm(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('invalid');
                isValid = false;
            } else {
                field.classList.remove('invalid');
            }
        });

        return isValid;
    }

    displayRecommendation(container, recommendation) {
        const { fertilizer, confidence, inputs } = recommendation;
        
        container.innerHTML = `
            <div class="result-content">
                <div class="fertilizer-icon">🌿</div>
                <div class="result-text">
                    <h3>Recommended Fertilizer</h3>
                    <p><strong>${fertilizer}</strong></p>
                    <p>Confidence: <strong>${confidence.toFixed(1)}%</strong></p>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                    <div class="recommendation-details mt-2">
                        <p><small>Based on: ${inputs['Soil Type']} soil, ${inputs['Crop Type']} crop</small></p>
                        <p><small>NPK: ${inputs.Nitrogen}:${inputs.Phosphorus}:${inputs.Potassium}</small></p>
                    </div>
                </div>
            </div>
        `;
        
        container.style.display = 'block';
        container.className = 'result success';
    }

    calculateCarbonFootprint(data) {
        // Simplified carbon footprint calculation
        // Real implementation would use complex agricultural models
        const baseEmission = 2.5; // kg CO2 per kg fertilizer
        const fertilizerAmount = (data.area || 1) * 0.1; // Estimated fertilizer per hectare
        
        const totalEmission = fertilizerAmount * baseEmission;
        const treesToOffset = Math.ceil(totalEmission / 22); // 22kg CO2 per tree per year
        
        return {
            totalEmission: totalEmission.toFixed(2),
            fertilizerAmount: fertilizerAmount.toFixed(2),
            treesToOffset,
            recommendations: [
                'Consider organic fertilizers to reduce emissions',
                'Implement precision agriculture techniques',
                'Use cover crops to improve soil health'
            ]
        };
    }

    displayCarbonFootprint(container, data) {
        container.innerHTML = `
            <div class="result-content">
                <div class="fertilizer-icon">🌍</div>
                <div class="result-text">
                    <h3>Carbon Footprint Analysis</h3>
                    <p><strong>Estimated CO₂ Emission:</strong> ${data.totalEmission} kg</p>
                    <p><strong>Fertilizer Usage:</strong> ${data.fertilizerAmount} kg</p>
                    <p><strong>Trees to Offset:</strong> ${data.treesToOffset} trees/year</p>
                    <div class="mt-2">
                        <h4>Recommendations:</h4>
                        <ul>
                            ${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
        
        container.style.display = 'block';
        container.className = 'result success';
    }

    saveRecommendation(recommendation) {
        this.recommendations.unshift(recommendation);
        if (this.recommendations.length > 50) {
            this.recommendations = this.recommendations.slice(0, 50);
        }
        localStorage.setItem('agrosmartHistory', JSON.stringify(this.recommendations));
    }

    loadHistory() {
        const historyContainer = document.getElementById('historyContainer');
        if (historyContainer) {
            this.updateHistory();
        }
    }

    updateHistory() {
        const historyContainer = document.getElementById('historyContainer');
        if (!historyContainer) return;

        if (this.recommendations.length === 0) {
            historyContainer.innerHTML = '<p class="text-center">No recommendations yet.</p>';
            return;
        }

        const historyHTML = this.recommendations.slice(0, 10).map(rec => {
            const date = new Date(rec.timestamp).toLocaleDateString();
            const time = new Date(rec.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            return `
                <div class="history-item card mb-1">
                    <div class="history-header">
                        <strong>${rec.fertilizer}</strong>
                        <span class="timestamp">${date} ${time}</span>
                    </div>
                    <div class="history-details">
                        <p>Crop: ${rec.inputs['Crop Type']} | Soil: ${rec.inputs['Soil Type']}</p>
                        <p>Confidence: ${rec.confidence}%</p>
                    </div>
                </div>
            `;
        }).join('');

        historyContainer.innerHTML = historyHTML;
    }

    clearHistory() {
        if (confirm('Are you sure you want to clear all recommendation history?')) {
            this.recommendations = [];
            localStorage.removeItem('agrosmartHistory');
            this.updateHistory();
            this.showToast('History cleared successfully', 'success');
        }
    }

    exportData() {
        if (this.recommendations.length === 0) {
            this.showToast('No data to export', 'warning');
            return;
        }

        const csvData = this.convertToCSV(this.recommendations);
        const blob = new Blob([csvData], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `agromart-recommendations-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        this.showToast('Data exported successfully', 'success');
    }

    convertToCSV(data) {
        const headers = ['Date', 'Time', 'Fertilizer', 'Confidence', 'Crop Type', 'Soil Type', 'Temperature', 'Humidity', 'Moisture', 'Nitrogen', 'Phosphorus', 'Potassium'];
        
        const rows = data.map(rec => {
            const date = new Date(rec.timestamp);
            return [
                date.toLocaleDateString(),
                date.toLocaleTimeString(),
                rec.fertilizer,
                rec.confidence,
                rec.inputs['Crop Type'],
                rec.inputs['Soil Type'],
                rec.inputs.Temperature,
                rec.inputs.Humidity,
                rec.inputs.Moisture,
                rec.inputs.Nitrogen,
                rec.inputs.Phosphorus,
                rec.inputs.Potassium
            ];
        });

        return [headers, ...rows].map(row => row.map(field => `"${field}"`).join(',')).join('\n');
    }

    setButtonLoading(button, loading) {
        if (!button) return;
        
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
            button.setAttribute('data-original-text', button.textContent);
            button.textContent = 'Processing...';
        } else {
            button.classList.remove('loading');
            button.disabled = false;
            button.textContent = button.getAttribute('data-original-text') || 'Submit';
        }
    }

    showResult(container, message, type = 'info') {
        container.innerHTML = `<p class="${type === 'loading' ? 'loading-text' : ''}">${message}</p>`;
        container.style.display = 'block';
        container.className = `result ${type}`;
    }

    showError(container, message) {
        container.innerHTML = `<div class="error-text">❌ ${message}</div>`;
        container.style.display = 'block';
        container.className = 'result error';
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            background: ${type === 'success' ? 'var(--success)' : type === 'warning' ? 'var(--warning)' : 'var(--primary)'};
        `;

        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);

        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
}

// Initialize the application
const agroSmart = new AgroSmart();