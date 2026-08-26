from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import mysql
from app.models import db

with open("schema.sql", "w", encoding="utf-8") as handle:
    for table in db.metadata.sorted_tables:
        handle.write(str(CreateTable(table).compile(dialect=mysql.dialect())) + ";\n\n")
print("schema.sql generated")
