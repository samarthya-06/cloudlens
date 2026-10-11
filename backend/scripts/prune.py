"""Remove only expired CloudLens local demo reports; S3 lifecycle handles cloud copies."""

from datetime import UTC, datetime, timedelta

from app.config import Settings
from app.repository import Repository


def main():
    settings = Settings()
    repository = Repository(settings)
    cutoff = (datetime.now(UTC) - timedelta(days=7)).isoformat()
    with repository.connect() as db:
        rows = db.execute(
            "SELECT id FROM incidents WHERE created_at<? AND status IN ('completed','failed')",
            (cutoff,),
        ).fetchall()
        for row in rows:
            identifier = row["id"]
            if len(identifier) == 32 and all(c in "0123456789abcdef" for c in identifier):
                (settings.artifact_path / f"{identifier}.json").unlink(missing_ok=True)
        db.execute(
            "DELETE FROM incidents WHERE created_at<? AND status IN ('completed','failed')",
            (cutoff,),
        )
        db.execute("DELETE FROM sessions WHERE expires<?", (datetime.now(UTC).timestamp(),))
    print(f"Removed {len(rows)} expired local reports.")


if __name__ == "__main__":
    main()
