# Functionality Overview

## 📂 Project Structure
```
Intelligent Patient Health Risk Predictor/
├─ app.py                # Flask application, routes, models, utilities
├─ requirements.txt      # Python dependencies
├─ .env                  # Environment variables (secret keys, Twilio credentials)
├─ templates/
│   ├─ base.html        # Base layout, includes Chart.js, Bootstrap, navigation
│   ├─ index.html       # Dashboard with input form, analytics cards, charts, CSV upload
│   ├─ results.html     # Detailed results table with PDF export links
│   └─ ...
├─ static/
│   ├─ css/style.css    # Custom styling, CSS variables for premium UI
│   └─ js/main.js       # Front‑end logic – form validation, tooltips, chart init, loading overlay
└─ README.md            # Project description (generated earlier)
```

## 🗂️ Database Model (`app.py`)
```python
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default="doctor")
    is_active = db.Column(db.Boolean, default=True)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assessments = db.relationship("Assessment", backref="patient", lazy=True, cascade="all, delete-orphan")

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    features_json = db.Column(db.Text, nullable=False)   # JSON string of input features
    risk_score = db.Column(db.Float, nullable=False)    # Percentage (0‑100)
    risk_label = db.Column(db.String(50), nullable=False)  # "High Risk" / "Low Risk"
    is_high_risk = db.Column(db.Boolean, nullable=False)
    sms_status = db.Column(db.String(100), nullable=True)   # SID or error text
```
*`features_json`* stores the raw clinical measurements for auditability.

## 🚀 Core Backend Routes (`app.py`)
| Method | Route | Description |
|--------|-------|-------------|
| **GET** | `/login` | Render login page; POST validates credentials and creates a session. |
| **GET** | `/logout` | Ends the user session and redirects to login. |
| **GET** | `/` (dashboard) | Shows recent predictions, analytics stats (`total`, `high`, `low`, `ratio`) and supplies JSON data (`risk_stats`, `risk_trend`) for Chart.js. |
| **POST** | `/predict` | Handles the single‑patient form. Validates fields, runs the model, stores an `Assessment`, optionally sends a Twilio SMS for high‑risk cases, then redirects back to the dashboard. |
| **POST** | `/upload` | **Phase 4 bulk CSV upload** – receives a CSV file, validates column headers (`patient_name` + the 10 model features), processes each row in a loop, creates `Patient`/`Assessment` records, sends SMS for high‑risk rows, and flashes a summary of successes/failures. |
| **GET** | `/export/<int:assessment_id>` | Generates a PDF using **ReportLab**: header, patient metadata, a table of features, risk label & score, recommendations, and a signature placeholder. Returns the file as an attachment. |
| **GET** | `/results` | Renders a full table of all assessments (identical to the dashboard table but without the input form) and includes a **PDF Export** button per row linking to the route above. |

## 📊 Front‑End Functionality (`templates/*` & `static/js/main.js`)
### Dashboard (`index.html`)
- **Input Form** – patient name + 10 numeric clinical fields. Validation uses Bootstrap validation + custom JavaScript (`initFormValidation`).
- **Batch CSV Card** – file input (`accept=".csv"`) posting to `/upload`.
- **Analytics Grid** – two `<canvas>` elements:
  - **Donut Chart** – displays the proportion of high‑risk vs low‑risk assessments (data from `risk_stats`).
  - **Line Chart** – plots each assessment’s `risk_score` over time (data from `risk_trend`).
- **Results Table** – colour‑coded rows (`high-risk-row` / `low-risk-row`), progress bars showing confidence, icons with hover tooltips, SMS status icons, and a **PDF Export** button linking to `/export/{{ pred.id }}`. 
- **Quick Stats Card** – total assessments and counts of high/low risk cases.

### Results Page (`results.html`)
- Mirrors the dashboard table but without the input form.
- Includes a **Back to Dashboard** button.
- Displays the same colour‑coded rows, progress bars, SMS status, and PDF export links.

### JavaScript (`main.js`)
- **initFormValidation** – Bootstrap‑style validation, shake animation on errors.
- **initAutoDismissAlerts** – Auto‑close flash messages after a configurable delay.
- **initProgressBars** – Animate progress bars when they enter the viewport.
- **initRiskRowAnimations** – Subtle slide‑in and pulse‑on‑hover for high‑risk rows.
- **initSmoothScroll** – Smooth scrolling for intra‑page anchors.
- **initInputFormatting** – Capitalises patient name on blur and restricts numeric inputs to a single decimal.
- **exportResultsToCSV** – Generates a CSV download of the visible table.
- **initLoadingOverlay** – Shows a custom spinner overlay while a prediction request is in progress.
- **Chart.js Integration** (`initCharts` – added in Phase 4):
  ```javascript
  const donutCtx = document.getElementById('riskRatioChart').getContext('2d');
  const lineCtx = document.getElementById('riskTrendChart').getContext('2d');
  const donutChart = new Chart(donutCtx, { type: 'doughnut', data: {...}, options: {...} });
  const lineChart = new Chart(lineCtx, { type: 'line', data: {...}, options: {...} });
  ```
  Data (`risk_stats` and `risk_trend`) is injected by Flask into the template context and parsed as JSON in the script.

## 📨 Twilio SMS Integration (`app.py`)
- `send_high_risk_sms(patient_name, risk_score)` builds a message with emojis, uses `Client` from `twilio.rest`, and returns the message SID.
- The route `/predict` and the bulk upload loop call this helper **only when `is_high_risk` is true**.
- SMS status (`assessment.sms_status`) is saved for later display; failure strings are prefixed with `SMS_FAILED:`.
- Future UI enhancements (Phase 2) include a **Retry SMS** button and a **global toggle** to disable alerts during testing.

## 📄 PDF Generation (`/export/<id>`)
- Uses **ReportLab** (`SimpleDocTemplate`, `Paragraph`, `Table`, `TableStyle`).
- Header → Patient name & timestamp → Features table → Risk assessment summary → Recommendations → Doctor signature placeholder.
- The PDF is streamed back with `send_file(..., as_attachment=True, download_name='assessment_<id>.pdf')`.

## 🛡️ Security & Best Practices
- **Environment variables** are validated at startup; missing variables raise a clear `RuntimeError`. (Fixed in the earlier patch.)
- Passwords stored as **bcrypt hashes** via `generate_password_hash`.
- Flask‑Login protects all routes except `/login` and `/static/*`.
- CSRF protection can be added later via `Flask‑WTF`.
- All external secrets (Twilio, Flask secret) are kept out of source control via `.gitignore`.

## 📦 Deployment Notes
- Development server runs on `python app.py` (debug mode). For production use a WSGI server such as **Gunicorn**:
  ```bash
  gunicorn -w 4 -b 0.0.0.0:5001 app:app
  ```
- The SQLite file (`health_predictor.db`) lives in the project root (`instance/` can be used for separation). Back‑up the DB regularly.
- Static assets are served via Flask’s built‑in static route; CDN links for Bootstrap, Chart.js, and icons keep the bundle light.

## 📚 Future Enhancements (Roadmap snippets)
- **Phase 2**: Add retry SMS button and global alert toggle.
- **Phase 3**: Implement background jobs for heavy CSV processing (Celery/RQ).
- **Phase 4** (current): Bulk upload, analytics charts, PDF export, UI tooltips.
- **Phase 5**: Role‑based dashboards (admin vs doctor), patient‑wise history view, export of aggregated reports.

---
*This file documents the complete functional surface of the Intelligent Patient Health Risk Predictor, delivering a clear reference for developers, reviewers, and future contributors.*
