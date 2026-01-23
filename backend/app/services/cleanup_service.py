import time
from pathlib import Path
from app.utils.logger import setup_logger

logger = setup_logger("cleanup_service")


class CleanupService:
    def __init__(self, upload_dir: str = "/app/uploads", max_age_hours: int = 24):
        self.upload_dir = Path(upload_dir)
        self.max_age_seconds = max_age_hours * 3600

    def cleanup_old_files(self) -> int:
        """Delete files older than max_age_hours"""
        if not self.upload_dir.exists():
            return 0

        deleted_count = 0
        current_time = time.time()

        for file_path in self.upload_dir.rglob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > self.max_age_seconds:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")

        # Clean up empty directories
        for dir_path in sorted(self.upload_dir.rglob("*"), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                except Exception:
                    pass

        if deleted_count > 0:
            logger.info(f"Cleanup completed: deleted {deleted_count} files")

        return deleted_count


cleanup_service = CleanupService()
