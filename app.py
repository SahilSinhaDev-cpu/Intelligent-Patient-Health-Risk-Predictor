import os
import joblib
import warnings
from datetime import datetime
import json

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import io
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------------
load_dotenv()

# Enforce required environment variables on startup
required_vars = [
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_PHONE_NUMBER",
    "DOCTOR_PHONE_NUMBER",
    "FLASK_SECRET_KEY"
]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
        raise RuntimeError(
        f"Configuration Error: Missing required environment variables in .env: {', '.join(missing_vars)}"
    )

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
DOCTOR_PHONE_NUMBER = os.getenv("DOCTOR_PHONE_NUMBER")

# ------------------------------------------------------------------
# Load trained model artifact
# ------------------------------------------------------------------
try:
    artifact = joblib.load("health_model.joblib")
    MODEL = artifact["model"]
    FEATURE_NAMES = artifact["feature_names"]
except Exception as e:
    print(f"CRITICAL: Failed to load model artifact: {e}")
    MODEL = None
    FEATURE_NAMES = []

# ------------------------------------------------------------------
# Flask app configuration
# ------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# SQLite Database setup
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///health_predictor.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Login manager configuration
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# ------------------------------------------------------------------
# Database Models
# ------------------------------------------------------------------
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="doctor")
    is_active = db.Column(db.Boolean, default=True)

class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assessments = db.relationship("Assessment", backref="patient", lazy=True, cascade="all, delete-orphan")

class Assessment(db.Model):
    __tablename__ = "assessments"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    features_json = db.Column(db.Text, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    risk_label = db.Column(db.String(50), nullable=False)
    is_high_risk = db.Column(db.Boolean, nullable=False)
    sms_status = db.Column(db.String(100), nullable=True)

    @property
    def features(self):
        try:
            return json.loads(self.features_json)
        except Exception:
            return {}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database and seed users
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role="admin"
        ))
    if not User.query.filter_by(username="doctor").first():
        db.session.add(User(
            username="doctor",
            password_hash=generate_password_hash("doctor123"),
            role="doctor"
        ))
    db.session.commit()

# ------------------------------------------------------------------
# Twilio SMS helper
# ------------------------------------------------------------------
def send_high_risk_sms(patient_name: str, risk_score: float) -> str:
    """Send SMS alert via Twilio. Returns message SID or error string."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        body = (
            f"🚨 HEALTH ALERT 🚨\n"
            f"Patient: {patient_name}\n"
            f"Risk Score: {risk_score:.2%}\n"
            f"AI Flag: HIGH RISK for malignancy.\n"
            f"Action: Schedule follow-up immediately.\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        message = client.messages.create(
            body=body,
            from_=TWILIO_PHONE_NUMBER,
            to=DOCTOR_PHONE_NUMBER,
        )
        return message.sid
    except Exception as e:
        return f"SMS_FAILED: {str(e)}"


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """Secure login screen."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome, Dr. {username.capitalize()}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    """Main dashboard — requires login."""
    # Fetch recent predictions and analytics stats
    recent_predictions = Assessment.query.join(Patient).order_by(Assessment.timestamp.desc()).limit(10).all()
    
    predictions_data = []
    for pred in recent_predictions:
        predictions_data.append({
            "timestamp": pred.timestamp.strftime("%Y-%m-%d %H:%M"),
            "patient_name": pred.patient.name,
            "risk_label": pred.risk_label,
            "risk_score": pred.risk_score,
            "is_high_risk": pred.is_high_risk,
            "sms_status": pred.sms_status,
            "id": pred.id
        })
    
    # Analytics data
    total = Assessment.query.count()
    high = Assessment.query.filter_by(is_high_risk=True).count()
    low = total - high
    risk_ratio = (high / total * 100) if total else 0
    # Trend data (list of [timestamp, risk_score])
    trend_qs = Assessment.query.order_by(Assessment.timestamp).all()
    risk_trend = [[a.timestamp.strftime("%Y-%m-%d %H:%M"), a.risk_score] for a in trend_qs]
    
    risk_stats = {"total": total, "high": high, "low": low, "ratio": risk_ratio}
    
    return render_template("index.html", username=current_user.username, predictions=predictions_data, risk_stats=risk_stats, risk_trend=risk_trend)


@app.route("/predict", methods=["POST"])
@login_required
def predict():
    """Single-patient predifunction initInputFormatting() {t."""
    try:
        # Extract form data
        patient_name = request.form.get("patient_name", "Unknown").strip()
        feature_values = []
        features_dict = {}

        for feat in FEATURE_NAMES:
            val = request.form.get(feat)
            if val is None or val.strip() == "":
                flash(f"Missing value for feature: {feat}", "danger")
                return redirect(url_for("dashboard"))
            val_float = float(val)
            feature_values.append(val_float)
            features_dict[feat] = val_float

        # Predict
        X_input = [feature_values]
        prediction = MODEL.predict(X_input)[0]          # 0 or 1
        risk_proba = MODEL.predict_proba(X_input)[0][1]  # Probability of High Risk

        result_label = "High Risk" if prediction == 1 else "Low Risk"
        is_high_risk = prediction == 1
        risk_score_percent = round(risk_proba * 100, 2)

        # Find or create patient
        patient = Patient.query.filter_by(name=patient_name).first()
        if not patient:
            patient = Patient(name=patient_name)
            db.session.add(patient)
            db.session.flush() # get the patient.id

        # Twilio alert for High Risk only
        sms_status = None
        if is_high_risk:
            sms_status = send_high_risk_sms(patient_name, risk_proba)
            app.logger.info(f"SMS Status for {patient_name}: {sms_status}")

        # Save to database
        assessment = Assessment(
            patient_id=patient.id,
            features_json=json.dumps(features_dict),
            risk_score=risk_score_percent,
            risk_label=result_label,
            is_high_risk=is_high_risk,
            sms_status=sms_status
        )
        db.session.add(assessment)
        db.session.commit()

        return redirect(url_for("dashboard"))

    except ValueError as ve:
        flash(f"Invalid numeric input: {str(ve)}", "danger")
        return redirect(url_for("dashboard"))
    except Exception as e:
        flash(f"Prediction error: {str(e)}", "danger")
        return redirect(url_for("dashboard"))


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    """CSV batch processing endpoint — placeholder for Phase 3 extension."""
    # Bulk CSV Upload handling
    if 'file' not in request.files:
        flash('No file part in the request', 'danger')
        return redirect(url_for('dashboard'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'warning')
        return redirect(url_for('dashboard'))
    try:
        stream = io.StringIO(file.stream.read().decode('UTF8'), newline=None)
        csv_reader = csv.DictReader(stream)
        required_columns = ['patient_name'] + FEATURE_NAMES
        missing = [col for col in required_columns if col not in csv_reader.fieldnames]
        if missing:
            flash(f'Missing columns in CSV: {", ".join(missing)}', 'danger')
            return redirect(url_for('dashboard'))
        success_count = 0
        fail_count = 0
        for row in csv_reader:
            try:
                patient_name = row['patient_name'].strip()
                feature_values = []
                features_dict = {}
                for feat in FEATURE_NAMES:
                    val = row[feat]
                    if val is None or val.strip() == '':
                        raise ValueError(f'Missing value for feature: {feat}')
                    val_float = float(val)
                    feature_values.append(val_float)
                    features_dict[feat] = val_float
                # Predict
                X_input = [feature_values]
                prediction = MODEL.predict(X_input)[0]
                risk_proba = MODEL.predict_proba(X_input)[0][1]
                result_label = "High Risk" if prediction == 1 else "Low Risk"
                is_high_risk = prediction == 1
                risk_score_percent = round(risk_proba * 100, 2)
                # Patient handling
                patient = Patient.query.filter_by(name=patient_name).first()
                if not patient:
                    patient = Patient(name=patient_name)
                    db.session.add(patient)
                    db.session.flush()
                sms_status = None
                if is_high_risk:
                    sms_status = send_high_risk_sms(patient_name, risk_proba)
                # Save assessment
                assessment = Assessment(
                    patient_id=patient.id,
                    features_json=json.dumps(features_dict),
                    risk_score=risk_score_percent,
                    risk_label=result_label,
                    is_high_risk=is_high_risk,
                    sms_status=sms_status
                )
                db.session.add(assessment)
                db.session.commit()
                success_count += 1
            except Exception as e:
                db.session.rollback()
                fail_count += 1
        flash(f'CSV processed: {success_count} successes, {fail_count} failures.', 'info')
    except Exception as e:
        flash(f'Error processing CSV: {str(e)}', 'danger')
    return redirect(url_for('dashboard'))


@app.route("/results")
@login_required
def results():
    """Dedicated results page showing all prediction history."""
    # Pass analytics data to results page as well
    all_assessments = Assessment.query.join(Patient).order_by(Assessment.timestamp.desc()).all()
    predictions_data = []
    for pred in all_assessments:
        predictions_data.append({
            "timestamp": pred.timestamp.strftime("%Y-%m-%d %H:%M"),
            "patient_name": pred.patient.name,
            "risk_label": pred.risk_label,
            "risk_score": pred.risk_score,
            "is_high_risk": pred.is_high_risk,
            "sms_status": pred.sms_status,
            "id": pred.id
        })
    
    # Analytics for results page (optional)
    total = Assessment.query.count()
    high = Assessment.query.filter_by(is_high_risk=True).count()
    low = total - high
    risk_ratio = (high / total * 100) if total else 0
    trend_qs = Assessment.query.order_by(Assessment.timestamp).all()
    risk_trend = [[a.timestamp.strftime("%Y-%m-%d %H:%M"), a.risk_score] for a in trend_qs]
    risk_stats = {"total": total, "high": high, "low": low, "ratio": risk_ratio}
    
    return render_template("results.html", predictions=predictions_data, risk_stats=risk_stats, risk_trend=risk_trend)

# ------------------------------------------------------------------
# Run server
# ------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)