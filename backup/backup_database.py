import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse, unquote

from dotenv import load_dotenv


# Load project environment variables
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


BACKUP_DIR = PROJECT_ROOT / "backup" / "files"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def find_mysqldump():
    """Find mysqldump on Windows."""
    possible_paths = [
        Path(r"C:\Program Files\MySQL\MySQL Server 9.6\bin\mysqldump.exe"),
        Path(r"C:\Program Files\MySQL\MySQL Server 9.5\bin\mysqldump.exe"),
        Path(r"C:\Program Files\MySQL\MySQL Server 9.4\bin\mysqldump.exe"),
        Path(r"C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqldump.exe"),
        Path(r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"),
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)

    return "mysqldump"


def parse_database_url():
    """Read MySQL connection details from DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing from .env")

    parsed = urlparse(database_url)

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": parsed.username or "root",
        "password": unquote(parsed.password or ""),
        "database": parsed.path.lstrip("/"),
    }


def create_backup():
    config = parse_database_url()

    dump_tool = find_mysqldump()

    timestamp = __import__("datetime").datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_file = BACKUP_DIR / (
        f"disaster_management_backup_{timestamp}.sql"
    )

    command = [
        dump_tool,
        "--host",
        config["host"],
        "--port",
        str(config["port"]),
        "--user",
        config["user"],
        "--password=" + config["password"],
        "--single-transaction",
        "--routines",
        "--triggers",
        config["database"],
    ]

    print("Creating database backup...")
    print(f"Database: {config['database']}")
    print(f"Output: {backup_file}")

    with backup_file.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            command,
            stdout=output,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )

    if result.returncode != 0:
        backup_file.unlink(missing_ok=True)

        raise RuntimeError(
            "Backup failed:\n"
            + result.stderr
        )

    print()
    print("Backup created successfully.")
    print(f"File: {backup_file}")


if __name__ == "__main__":
    create_backup()