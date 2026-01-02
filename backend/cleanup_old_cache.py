"""
Script to clean up old comparison_cache entries from Supabase.
Deletes entries older than 1 day.
This should be run as a scheduled task (cron job).
"""
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from lib.supabase_client import supabase_admin

# Load .env from project root (parent directory)
script_dir = Path(__file__).parent
project_root = script_dir.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)


def cleanup_old_comparison_cache():
    """Delete comparison_cache entries older than 1 day"""
    try:
        if not supabase_admin:
            print(
                "supabase_admin not available, "
                "skipping comparison_cache cleanup"
            )
            return 0

        # Get entries older than 1 day
        cutoff_date = (datetime.now() - timedelta(days=1)).isoformat()

        # First, count how many will be deleted
        count_response = (
            supabase_admin.table("comparison_cache")
            .select("session_id", count="exact")
            .lt("created_at", cutoff_date)
            .execute()
        )

        total_to_delete = (
            count_response.count if hasattr(count_response, 'count') else 0
        )

        if total_to_delete == 0:
            print("No old comparison_cache entries to delete.")
            return 0

        # Delete entries older than 1 day
        delete_response = (
            supabase_admin.table("comparison_cache")
            .delete()
            .lt("created_at", cutoff_date)
            .execute()
        )

        # Count deleted entries
        deleted_count = (
            len(delete_response.data)
            if delete_response.data
            else total_to_delete
        )

        print(
            f"Comparison cache cleanup completed. "
            f"Deleted {deleted_count} entries."
        )
        return deleted_count

    except Exception as e:
        print(f"Error during comparison_cache cleanup: {str(e)}")
        raise


if __name__ == "__main__":
    cleanup_old_comparison_cache()
