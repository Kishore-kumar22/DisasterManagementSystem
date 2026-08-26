import csv
from datetime import datetime
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models import Disaster, User, DisasterStatusHistory
from app.disasters.routes import recalculate_score

app = create_app()
CSV_PATH = Path(__file__).with_name("disasters.csv")


def import_csv():
    with app.app_context():
        reporter = User.query.filter_by(role="admin").first()
        if not reporter:
            raise RuntimeError("Seed an admin account before importing CSV records.")
        added = 0
        with CSV_PATH.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                incident = Disaster(
                    title=row["title"],
                    disaster_type=row["disaster_type"],
                    description=row["description"],
                    severity=row["severity"],
                    affected_population=int(row["affected_population"]),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    status=row["status"],
                    occurred_at=datetime.fromisoformat(row["occurred_at"]),
                    reported_by=reporter.id,
                )
                db.session.add(incident)
                db.session.flush()
                recalculate_score(incident)
                db.session.add(DisasterStatusHistory(disaster_id=incident.id, changed_by=reporter.id, new_status="Reported", changed_at=incident.occurred_at, remarks="Imported from synthetic CSV dataset."))
                if incident.status != "Reported":
                    db.session.add(DisasterStatusHistory(disaster_id=incident.id, changed_by=reporter.id, old_status="Reported", new_status=incident.status, changed_at=incident.occurred_at, remarks="Imported status."))
                added += 1
        db.session.commit()
        print(f"Imported {added} disaster records from {CSV_PATH.name}.")


if __name__ == "__main__":
    import_csv()
