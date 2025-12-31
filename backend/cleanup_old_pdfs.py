"""
Script to clean up PDFs older than 7 days from Supabase Storage and database.
This should be run as a scheduled task (cron job).
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from lib.supabase_client import supabase_admin

load_dotenv()


def cleanup_old_pdfs():
    """Delete PDFs older than 7 days"""
    try:
        # Get PDFs older than 7 days from database
        cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
        
        response = supabase_admin.table("pdfs").select("id, pdf_path").lt("created_at", cutoff_date).execute()
        
        deleted_count = 0
        for pdf_record in response.data:
            pdf_id = pdf_record["id"]
            pdf_path = pdf_record["pdf_path"]
            
            try:
                # Delete from storage
                supabase_admin.storage.from_("pdfs").remove([pdf_path])
                
                # Delete from database
                supabase_admin.table("pdfs").delete().eq("id", pdf_id).execute()
                
                deleted_count += 1
                print(f"Deleted PDF: {pdf_path}")
            except Exception as e:
                print(f"Error deleting PDF {pdf_path}: {str(e)}")
        
        print(f"Cleanup completed. Deleted {deleted_count} PDFs.")
        return deleted_count
        
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        raise


if __name__ == "__main__":
    cleanup_old_pdfs()

