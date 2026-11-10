from app.database import SessionLocal
from app.routers.resumes import UPLOAD_DIR
from app.services.resume_retention import (
    delete_expired_resumes,
    delete_expired_upload_files,
)


def main() -> None:
    db = SessionLocal()
    try:
        deleted_resumes = delete_expired_resumes(db)
        db.commit()
        deleted_files = delete_expired_upload_files(UPLOAD_DIR)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Deleted {deleted_resumes} expired resume records and {deleted_files} stale upload files.")


if __name__ == "__main__":
    main()
