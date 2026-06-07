# Intelligent Patient Health Risk Predictor

![Dashboard Mockup](/Users/sahilkumarsinha/.gemini/antigravity-ide/brain/7d41080f-af09-4990-8205-b3423840160e/dashboard_mockup_1780851838271.png)

## 🎯 Vision
A cutting‑edge AI‑powered web application that predicts breast cancer risk (or similar health concerns) from clinical measurements, alerts physicians via **Twilio SMS**, and delivers **PDF clinical summaries**. Designed for clinicians who need fast, reliable, and actionable risk insights.

## ✨ Key Features
- **Real‑time single‑patient prediction** with beautiful UI and animated risk bars.
- **Bulk CSV upload** for batch predictions (Phase 4).
- **Dynamic analytics dashboard** using **Chart.js** – donut chart for risk ratio and line chart for temporal trends.
- **PDF export** of assessment reports (ReportLab).
- **Secure login** with role‑based access (`admin`, `doctor`).
- **Twilio SMS alerts** for high‑risk patients, with retry/failure handling.
- **Responsive design** – mobile‑friendly, dark‑mode ready, glass‑morphism accents.
- **Extensible architecture** – Flask, SQLAlchemy (SQLite), Joblib model artifact.

## 🛠️ Tech Stack
| Layer | Technology |
|------|------------|
| Backend | Python 3.12, Flask 3.0, Flask‑Login, Flask‑SQLAlchemy |
| ML Model | Scikit‑learn, Joblib |
| Database | SQLite (self‑contained) |
| Frontend | HTML5, Bootstrap 5.3, Chart.js, vanilla JS |
| PDF Generation | ReportLab |
| SMS | Twilio SDK |
| Environment | python‑dotenv |

## 🚀 Quick Start
```bash
# Clone the repo (already in your workspace)
cd "Intelligent Patient Health Risk Predictor"
# Create virtual environment
python -m venv venv && source venv/bin/activate
# Install dependencies
pip install -r requirements.txt
# Set environment variables (copy .env.example → .env and edit)
cp .env.example .env
# Edit .env with your secrets (Flask key, Twilio creds, doctor phone)
# Initialise DB and seed users (admin / doctor)
python -c "import app;"  # runs DB init on import
# Run the server
python app.py
```
The app will be available at **http://localhost:5001**.

## 📋 Environment Variables (`.env`)
```dotenv
FLASK_SECRET_KEY=your‑super‑secret‑key
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX
DOCTOR_PHONE_NUMBER=+91XXXXXXXXXX
```
> **Tip:** Keep the `.env` file out of version control.

## 🔗 API Endpoints
| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/` | Dashboard – recent assessments & analytics |
| POST | `/predict` | Single‑patient form submission |
| POST | `/upload` | Bulk CSV upload (Phase 4) |
| GET | `/export/<int:id>` | Download PDF report for an assessment |
| GET | `/results` | Full history table |
| GET/POST | `/login`, `/logout` | Authentication |

## 📊 Analytics (Phase 4)
- **Donut Chart** – visualises the high‑risk vs low‑risk ratio.
- **Line Chart** – plots risk scores over time for the selected patient cohort.
- Both charts update automatically after each new prediction.

## 📄 PDF Report Layout
The generated PDF includes:
1. Header with project branding
2. Patient details & timestamp
3. Table of clinical measurements
4. Prediction result & risk score
5. Recommendations & next‑step guidance
6. Doctor signature placeholder

## 🧩 Extending the Project
- **Add new models** – drop a `model.pkl` and update `FEATURE_NAMES`.
- **Swap SQLite for Postgres** – change the DB URI in `app.py`.
- **Deploy** – containerise with Docker, expose port 5000, set `FLASK_ENV=production`.
- **CI/CD** – integrate tests with GitHub Actions; run `pytest` on push.

## 🧪 Testing
```bash
# Run unit tests (if added)
pytest
# Manual test flow
1. Login as `doctor` (password `doctor123`).
2. Submit a patient record → see risk visualisation.
3. If high‑risk, ensure an SMS is sent (check Twilio console).
4. Upload a CSV with multiple rows → verify batch results.
5. Click “Export PDF” on a result row → open the PDF.
```

## 👥 Contributors
- **Sahil Kumar Sinha** – Project architect & lead developer
- **AI‑Assisted Development** – Generated UI/UX design, documentation, and rapid prototyping.

---
*Built with love, ambition, and a drive to empower clinicians with AI.*
