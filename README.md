# Cloud-Based Disaster Management and Emergency Response Analytics System

A complete undergraduate-level Flask and MySQL prototype for disaster incident reporting, transparent priority scoring, response coordination, resource allocation, in-application alerts, map monitoring, and operational analytics.

## Technology stack

The project uses Python 3, Flask, Flask-SQLAlchemy, MySQL through PyMySQL, Werkzeug password hashing, Bootstrap 5, vanilla JavaScript, Chart.js, Leaflet.js, and Pandas. The frontend libraries are loaded from CDNs, so the browser needs internet access when the application is opened unless those assets are later downloaded and served locally.

The architecture is intentionally a simple modular monolith. Flask routes handle requests, SQLAlchemy models represent relational data, service modules contain business rules, Pandas transforms bounded MySQL query results, and JSON endpoints provide data to Chart.js and Leaflet.

## Windows setup in VS Code

### 1. Install prerequisites

Install Python 3.11 or newer, MySQL Server 8.x, and Visual Studio Code. During Python installation, select **Add Python to PATH**. Verify the installations in PowerShell:

```powershell
python --version
mysql --version
```

### 2. Open the project

Extract the ZIP file and open the extracted `DisasterManagementSystem` folder in VS Code. Open a PowerShell terminal at the project root, the folder containing `run.py`.

### 3. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, either run the project from Command Prompt using `.venv\Scripts\activate.bat`, or allow local scripts for your user account:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Activate the environment again after changing the policy.

### 4. Install Python dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Create the MySQL database

Open MySQL Workbench or a MySQL client and run:

```sql
CREATE DATABASE disaster_management
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

If you prefer a dedicated MySQL user, run the following as a MySQL administrator and replace the password with your own value:

```sql
CREATE USER 'disaster_app'@'localhost' IDENTIFIED BY 'ChangeThisPassword!';
GRANT ALL PRIVILEGES ON disaster_management.* TO 'disaster_app'@'localhost';
FLUSH PRIVILEGES;
```

### 6. Configure environment variables

From PowerShell, copy the example file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set the values. With the dedicated user, the database URL can be:

```text
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=mysql+pymysql://disaster_app:ChangeThisPassword%21@localhost:3306/disaster_management
```

The `%21` is the URL-encoded form of `!`. If your password contains other special characters, URL-encode them in the database URL. A simple local password without URL-special characters is easier for a first run.

### 7. Initialize and seed the database

The application factory creates tables automatically, while the seed script resets the schema and loads meaningful synthetic data, demo accounts, responses, allocations, alerts, and status history:

```powershell
python -m seed.seed_data
```

To import the additional synthetic CSV dataset after seeding:

```powershell
python -m seed.import_csv
```

The seed script is destructive because it calls `drop_all()` before recreating the schema. Use it only for a fresh demonstration database. The CSV importer appends records and can be run more than once, so avoid repeated imports unless duplicate historical rows are intentional.

### 8. Run the application

```powershell
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser. Stop the server with `Ctrl+C`.

For a production-like startup test, the installed Flask CLI can also run:

```powershell
flask --app run.py run
```

The built-in server is intended for local development. A later cloud deployment should use the platform’s production Python/WSGI startup configuration.

## Demo credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `Admin@123` |
| Responder | `responder@example.com` | `Responder@123` |
| Responder | `nisha@example.com` | `Responder@123` |

Change these passwords before using the project outside a classroom demonstration.

## Core modules

The `users` table stores hashed passwords and roles. The `disasters` table stores incident facts, coordinates, lifecycle status, score components, final score, and category. The `resources` table stores total and available inventory. `responses` assigns responders to incidents, and `response_resources` implements the many-to-many relationship between response assignments and resource items. `alerts` provides in-application broadcasts. `disaster_status_history` records every status transition, while `audit_logs` records important actions.

The resource allocation route checks that the requested quantity is positive and no greater than the current available quantity. It then decreases availability, synchronizes the resource status, recalculates the affected incident’s priority score, and commits the operation. The route rejects insufficient quantities and never permits a negative value.

## Priority scoring

The score is calculated in `app/disasters/scoring.py`:

```text
priority_score =
    0.50 × severity_component +
    0.30 × population_component +
    0.20 × shortage_component
```

Each component is normalized to 0–5. Severity maps to Low=1, Medium=2, High=4, and Critical=5. Population uses documented thresholds: 0 people maps to 0, up to 100 maps to 1, up to 500 maps to 2, up to 1,000 maps to 3, up to 5,000 maps to 4, and above 5,000 maps to 5. The shortage component is the allocated-to-capacity ratio for resources assigned to that incident multiplied by 5 and clamped to 5.

The categories are LOW for 0.00–1.99, MEDIUM for 2.00–3.49, HIGH for 3.50–4.24, and CRITICAL for 4.25–5.00. This is an explainable prototype heuristic and is not a validated emergency-services standard.

## Analytics flow

The analytics route in `app/analytics/routes.py` queries MySQL through SQLAlchemy, constructs Pandas DataFrames, groups and transforms the records, and returns JSON. `app/static/js/app.js` passes that JSON into Chart.js. The implemented analytics include incidents by type, incidents by month, incidents by severity, response-status counts, affected population by month, average assignment-to-start response time, unresolved incidents, resource availability, and resource utilization by category.

The project demonstrates operational analytics at prototype scale. It does not claim distributed Big Data processing and intentionally does not use Hadoop, Spark, streaming infrastructure, or machine learning.

## Tests

Run the test suite from the project root:

```powershell
pytest -q
```

The tests use an in-memory SQLite database, so a separate test MySQL schema is not required. They cover login, unauthorized access, responder authorization, priority scoring, disaster creation, dashboard/analytics responses, and over-allocation rejection.

## Cloud deployment preparation

The code is prepared for later deployment because the secret key and database URL are read from environment variables, configuration is separated from routes, and the project does not depend on a local hard-coded database path. A cloud deployment should provide a managed MySQL database, set `DATABASE_URL` and `SECRET_KEY` in the platform’s secret configuration, install `requirements.txt`, and start the application with a production WSGI command appropriate to the selected platform. The current package does not automatically deploy anywhere.

## Five-to-seven-minute final demonstration

Start by explaining that the system is a cloud-ready coordination and analytics prototype, not an official emergency command system. Log in as the admin, show the role-aware navigation, create a new incident with coordinates, severity, and affected population, and open its detail page. Explain the three score components and the final priority category.

Next, assign a responder, allocate an ambulance or medical kit, and show the resource quantity decreasing. Attempt an allocation larger than the remaining quantity to demonstrate that the system rejects it. Publish an in-application alert linked to the incident and update the incident status so the status history records the change.

Finish with the dashboard KPIs, Chart.js charts, and Leaflet markers. Open the analytics page to show the explicit MySQL → Pandas → JSON → Chart.js path, then state the limitations: the sample data is synthetic, the alerts are in-application only, the score is a transparent heuristic, and the application is not a replacement for official emergency protocols.

## Known limitations

The project does not integrate SMS, WhatsApp, email, sensor feeds, satellite feeds, routing, evacuation optimization, machine learning, distributed processing, multi-region failover, or offline synchronization. The map depends on external OpenStreetMap tiles, and the dashboard’s periodic refresh is manual unless a browser polling loop is added later. The seed script is intentionally destructive for repeatable demonstrations. The application is suitable for local review and later cloud deployment preparation, but it requires production hardening before handling real personal or operational emergency data.
