# Final review demo script

## 0:00–0:35 — Problem and scope

Explain that Responda is a cloud-ready web prototype that connects incident reporting, resource coordination, transparent prioritization, in-application alerts, and operational analytics. State that it is decision support and not a replacement for official emergency protocols.

## 0:35–1:10 — Authentication

Log in as `admin@example.com` with `Admin@123`. Point out the role-aware navigation. Mention that passwords are stored as Werkzeug hashes and that administrative routes are protected by role checks.

## 1:10–2:00 — Report an incident

Create a flood or fire incident with a title, severity, affected population, description, and latitude/longitude. Open the detail screen and show that the record came from the database.

## 2:00–2:45 — Explainable priority score

Show the severity, population, and shortage component values, the formula, the final score, and the category. Explain that the score is deterministic and configurable rather than a machine-learning prediction.

## 2:45–3:35 — Response and allocation

Assign a responder, allocate an ambulance or medical kit, and show the remaining inventory quantity. Attempt an allocation larger than the available quantity to demonstrate the rejection message and no-negative safeguard.

## 3:35–4:15 — Status and alert workflow

Update the incident from Reported to Responding and show the status-history entry. Publish an in-application emergency alert linked to the incident and show it on the alerts page.

## 4:15–5:15 — Dashboard

Return to the dashboard. Show database-driven KPI cards, recent incidents, priority queue, and active alerts. Point out that the map markers come from `/disasters/api/map-data`.

## 5:15–6:00 — Charts and map

Show the incident-type and severity charts, then open the analytics page. Explain the MySQL → Pandas → JSON → Chart.js flow. Open a Leaflet marker and show its incident details.

## 6:00–6:40 — Cloud readiness

Explain that credentials are environment-based and that the same project can be connected to a managed MySQL instance and production WSGI host later. Do not claim high availability or multi-region recovery unless configured separately.

## 6:40–7:00 — Limitations

State that the sample data is synthetic, alerts are in-application only, the score is a prototype heuristic, and the project does not use external feeds, machine learning, or distributed Big Data infrastructure.
