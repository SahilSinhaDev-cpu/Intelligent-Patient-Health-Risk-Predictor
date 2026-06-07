/**
 * Intelligent Patient Health Risk Predictor
 * Main JavaScript Module
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // Initialize all modules
    // ==========================================
    initFormValidation();
    initAutoDismissAlerts();
    initProgressBars();
    initRiskRowAnimations();
    initSmoothScroll();
    initInputFormatting();
    
    console.log('🩺 Health Risk Predictor initialized');
});

// ==========================================
// Form Validation
// ==========================================
function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                shakeElement(form);
            }
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation feedback
    const inputs = document.querySelectorAll('input[type="number"]');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateNumericInput(this);
        });
        
        input.addEventListener('input', function() {
            clearErrorState(this);
        });
    });
}

function validateNumericInput(input) {
    const value = parseFloat(input.value);
    const min = parseFloat(input.min) || -Infinity;
    const max = parseFloat(input.max) || Infinity;
    
    if (isNaN(value)) {
        showInputError(input, 'Please enter a valid number');
        return false;
    }
    
    if (value < min || value > max) {
        showInputError(input, `Value must be between ${min} and ${max}`);
        return false;
    }
    
    return true;
}

function showInputError(input, message) {
    input.classList.add('is-invalid');
    
    let feedback = input.parentElement.querySelector('.invalid-feedback');
    if (!feedback) {
        feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        input.parentElement.appendChild(feedback);
    }
    feedback.textContent = message;
}

function clearErrorState(input) {
    input.classList.remove('is-invalid');
    const feedback = input.parentElement.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}

// ==========================================
// Auto-dismiss Alerts
// ==========================================
function initAutoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
    
    alerts.forEach(alert => {
        const delay = parseInt(alert.dataset.autoDismiss) || 5000;
        
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, delay);
    });
}

// ==========================================
// Animated Progress Bars
// ==========================================
function initProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const bar = entry.target;
                const targetWidth = bar.style.width;
                bar.style.width = '0%';
                
                setTimeout(() => {
                    bar.style.width = targetWidth;
                }, 200);
                
                observer.unobserve(bar);
            }
        });
    }, { threshold: 0.5 });
    
    progressBars.forEach(bar => observer.observe(bar));
}

// ==========================================
// Risk Row Animations
// ==========================================
function initRiskRowAnimations() {
    const highRiskRows = document.querySelectorAll('.high-risk-row');
    
    highRiskRows.forEach((row, index) => {
        row.style.animationDelay = `${index * 0.1}s`;
        row.classList.add('animate-slide-in');
        
        // Add pulse effect on hover
        row.addEventListener('mouseenter', function() {
            this.style.animation = 'none';
            setTimeout(() => {
                this.style.animation = 'riskPulse 2s ease-in-out infinite';
            }, 10);
        });
    });
    
    const lowRiskRows = document.querySelectorAll('.low-risk-row');
    lowRiskRows.forEach((row, index) => {
        row.style.animationDelay = `${index * 0.1}s`;
        row.classList.add('animate-slide-in');
    });
}

// ==========================================
// Smooth Scroll
// ==========================================
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ==========================================
// Input Formatting
// ==========================================
function initInputFormatting() {
    // Auto-capitalize patient name
    const nameInput = document.querySelector('input[name="patient_name"]');
    if (nameInput) {
        nameInput.addEventListener('blur', function() {
            this.value = this.value.replace(/\b\w/g, l => l.toUpperCase());
        });
    }
    
    // Restrict decimal places for clinical measurements
    const clinicalInputs = document.querySelectorAll('input[name^="mean "], input[name$=" error"], input[name^="worst "]');
    clinicalInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Allow only numbers and one decimal point
            this.value = this.value.replace(/[^0-9.]/g, '').replace(/(\..*)\./g, '$1');
        });
    });
}

// ==========================================
// Utility Functions
// ==========================================

/**
 * Shake an element to indicate error
 */
function shakeElement(element) {
    element.style.animation = 'shake 0.5s ease-in-out';
    setTimeout(() => {
        element.style.animation = '';
    }, 500);
}

/**
 * Show a toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show animate-slide-in`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(toast);
        bsAlert.close();
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 350px;
    `;
    document.body.appendChild(container);
    return container;
}

/**
 * Confirm high-risk action before submission
 */
function confirmHighRiskSubmission(patientName) {
    return confirm(
        `⚠️ HIGH RISK DETECTED\n\n` +
        `Patient: ${patientName}\n` +
        `This will trigger an SMS alert to the doctor.\n\n` +
        `Proceed with assessment?`
    );
}

/**
 * Export results to CSV
 */
function exportResultsToCSV() {
    const rows = document.querySelectorAll('table tbody tr');
    if (rows.length === 0) {
        showToast('No results to export', 'warning');
        return;
    }
    
    let csv = 'Time,Patient Name,Risk Level,Risk Score\n';
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 4) {
            const time = cells[0].textContent.trim();
            const name = cells[1].textContent.trim();
            const risk = cells[2].textContent.trim();
            const score = cells[3].textContent.trim().replace('%', '');
            csv += `"${time}","${name}","${risk}","${score}"\n`;
        }
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `health-risk-results-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    
    showToast('Results exported successfully', 'success');
}

// Add shake animation to stylesheet dynamically
// ==========================================
// Loading Spinner for Prediction Form
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    initLoadingSpinner();
});

function initLoadingSpinner() {
    const predictForm = document.querySelector('form[action="/predict"]');
    if (!predictForm) return;
    
    predictForm.addEventListener('submit', function(event) {
        // Validate form first
        if (!predictForm.checkValidity()) {
            return; // Let browser handle validation
        }
        
        showLoadingOverlay();
    });
}

function showLoadingOverlay() {
    // Create overlay if it doesn't exist
    let overlay = document.getElementById('prediction-loading-overlay');
    
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'prediction-loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="medical-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <i class="bi bi-heart-pulse-fill spinner-icon"></i>
                </div>
                <h5 class="loading-title">Analyzing Patient Data</h5>
                <p class="loading-subtitle">AI model is processing risk assessment...</p>
                <div class="loading-progress">
                    <div class="loading-progress-bar"></div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }
    
    overlay.classList.add('active');
    
    // Animate progress bar
    const progressBar = overlay.querySelector('.loading-progress-bar');
    if (progressBar) {
        setTimeout(() => progressBar.style.width = '60%', 200);
        setTimeout(() => progressBar.style.width = '90%', 800);
    }
}

// Hide overlay when page reloads (new prediction result loads)
window.addEventListener('beforeunload', function() {
    const overlay = document.getElementById('prediction-loading-overlay');
    if (overlay) overlay.classList.remove('active');
});