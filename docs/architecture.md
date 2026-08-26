# Architecture notes

The application is a modular Flask monolith. The browser contains Bootstrap markup, vanilla JavaScript, Chart.js charts, and Leaflet map controls. Flask blueprints separate authentication, incidents, resources, alerts, and analytics. SQLAlchemy models provide the relational data layer. The scoring service is isolated so the formula can be tested independently.

```text
Browser -> Flask routes -> service/business rules -> SQLAlchemy -> MySQL
                        \-> Pandas analytics -> JSON -> Chart.js
                        \-> disaster map JSON -> Leaflet markers
```

The main integrated workflow is:

1. An authenticated admin or responder reports a disaster.
2. The incident is saved with a status-history entry and an initial priority score.
3. An admin assigns a responder and the incident can move to Responding.
4. A response assignment receives resource allocations.
5. The allocation route checks available quantity, rejects over-allocation, decrements inventory, and recalculates the score.
6. Dashboard KPIs, charts, alerts, tables, and map markers query current database records.

The project avoids unnecessary framework or infrastructure complexity. It does not use React, Node.js, Docker, microservices, Kubernetes, Hadoop, Spark, blockchain, IoT, external notification providers, or machine learning.
