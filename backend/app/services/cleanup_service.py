import time
from pathlib import Path
from app.utils.logger import setup_logger

logger = setup_logger("cleanup_service")


class CleanupService:
    def __init__(
        self,
        upload_dir: str = "/app/uploads",
        cache_dir: str = "/app/cache",
        upload_max_age_hours: int = 24,
        cache_max_age_hours: int = 24
    ):
        self.upload_dir = Path(upload_dir)
        self.cache_dir = Path(cache_dir)
        self.upload_max_age_seconds = upload_max_age_hours * 3600
        self.cache_max_age_seconds = cache_max_age_hours * 3600

    def cleanup_old_files(self) -> int:
        """Delete files older than max_age_hours from uploads and cache"""
        total_deleted = 0

        # Cleanup uploads
        total_deleted += self._cleanup_directory(
            self.upload_dir,
            self.upload_max_age_seconds,
            "uploads"
        )

        # Cleanup cache
        total_deleted += self._cleanup_directory(
            self.cache_dir,
            self.cache_max_age_seconds,
            "cache"
        )

        return total_deleted

    def _cleanup_directory(self, directory: Path, max_age_seconds: int, name: str) -> int:
        """Clean up old files from a specific directory"""
        if not directory.exists():
            return 0

        deleted_count = 0
        current_time = time.time()

        for file_path in directory.rglob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old {name} file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")

        # Clean up empty directories
        for dir_path in sorted(directory.rglob("*"), reverse=True):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                except Exception:
                    pass

        if deleted_count > 0:
            logger.info(f"{name.capitalize()} cleanup completed: deleted {deleted_count} files")

        return deleted_count


cleanup_service = CleanupService()
