import hashlib
import io
import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from lib.document_processor import extract_text_from_input
from lib.gemini_client import analyze_cv, analyze_job_offer, compare_cv_and_offer
from lib.pdf_generator import generate_pdf
from lib.supabase_client import supabase_admin, supabase_client

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Career Assistant API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3100", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store processing status (in production, use Redis or similar)
# Structure: {process_id: {status, tasks, results, pdf_buffer}}
processing_status = {}


@app.get("/")
async def root():
    return {"message": "Career Assistant API"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify Supabase configuration"""
    health_status = {
        "status": "ok",
        "supabase": {
            "url_configured": bool(os.getenv("SUPABASE_URL")),
            "anon_key_configured": bool(os.getenv("SUPABASE_ANON_KEY")),
            "service_key_configured": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")),
        }
    }

    return health_status


def generate_hash(text: str) -> str:
    """Generate SHA256 hash of text content"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


async def get_cached_comparison(
    session_id: str,
    cv_text_hash: str,
    job_offer_text_hash: str,
    additional_considerations_hash: str | None
) -> dict | None:
    """Check if comparison results exist in cache"""
    try:
        # Use admin client to bypass RLS
        client = supabase_admin if supabase_admin else supabase_client
        query = client.table("comparison_cache").select("*").eq("session_id", session_id)
        result = query.execute()

        if result.data and len(result.data) > 0:
            cached = result.data[0]
            # Verify hashes match
            if (
                cached["cv_text_hash"] == cv_text_hash and
                cached["job_offer_text_hash"] == job_offer_text_hash and
                cached.get("additional_considerations_hash") == additional_considerations_hash
            ):
                logger.info(f"Cache hit for session_id: {session_id}")
                return cached["comparison_results"]

        return None
    except Exception as e:
        logger.warning(f"Error checking cache: {str(e)}")
        return None


async def save_comparison_to_cache(
    session_id: str,
    cv_text_hash: str,
    job_offer_text_hash: str,
    additional_considerations_hash: str | None,
    comparison_results: dict,
    cv_analysis: str | None = None,
    job_offer_analysis: str | None = None
):
    """Save comparison results to cache including analyses for PDF generation"""
    try:
        # Use admin client to bypass RLS
        if not supabase_admin:
            logger.warning("supabase_admin not available, cannot save to cache")
            return

        supabase_admin.table("comparison_cache").upsert({
            "session_id": session_id,
            "cv_text_hash": cv_text_hash,
            "job_offer_text_hash": job_offer_text_hash,
            "additional_considerations_hash": additional_considerations_hash,
            "comparison_results": comparison_results,
            "cv_analysis": cv_analysis,
            "job_offer_analysis": job_offer_analysis
        }).execute()
        logger.info(f"Comparison saved to cache for session_id: {session_id}")
    except Exception as e:
        logger.warning(f"Error saving to cache: {str(e)}")
        # Don't fail the request if cache save fails


def log_task(task_name: str):
    """Helper to log task start"""
    logger.info('--------------------------------')
    logger.info(f"Task: {task_name}")
    logger.info('--------------------------------')


def initialize_process_status(process_id: str):
    """Initialize processing status tracking"""
    processing_status[process_id] = {
        "status": "processing",
        "tasks": {
            "understand_cv": False,
            "understand_offer": False,
            "compare": False,
            "generate_pdf": False
        },
        "results": None
    }


async def analyze_documents(cv_text: str, job_offer_text: str, process_id: str):
    """Analyze CV and job offer documents"""
    log_task("Understand CV")
    processing_status[process_id]["tasks"]["understand_cv"] = True
    cv_analysis = await analyze_cv(cv_text)

    log_task("Understand Job Offer")
    processing_status[process_id]["tasks"]["understand_offer"] = True
    job_offer_analysis = await analyze_job_offer(job_offer_text)

    return cv_analysis, job_offer_analysis


async def get_cached_comparison_by_session_id(session_id: str) -> tuple[dict | None, str | None, str | None]:
    """Get cached comparison results by session_id only (without hash verification)
    Returns: (comparison_results, cv_analysis, job_offer_analysis)
    """
    try:
        client = supabase_admin if supabase_admin else supabase_client
        query = client.table("comparison_cache").select("*").eq("session_id", session_id)
        result = query.execute()

        if result.data and len(result.data) > 0:
            cached = result.data[0]
            logger.info(f"Found cached results for session_id: {session_id}")
            return (
                cached["comparison_results"],
                cached.get("cv_analysis"),
                cached.get("job_offer_analysis")
            )

        return None, None, None
    except Exception as e:
        logger.warning(f"Error checking cache by session_id: {str(e)}")
        return None, None, None


async def get_or_compute_comparison(
    cv_text: str | None,
    job_offer_text: str | None,
    additional_considerations: str | None,
    session_id: str | None,
    process_id: str
) -> tuple[dict, bool, str | None, str | None]:
    """
    Get comparison from cache or compute it.
    Returns: (comparison_results, from_cache, cv_analysis, job_offer_analysis)
    """
    # If only session_id is provided (no files), try to get from cache directly
    if session_id and not cv_text and not job_offer_text:
        cached_results, cached_cv_analysis, cached_job_offer_analysis = (
            await get_cached_comparison_by_session_id(session_id)
        )
        if cached_results:
            logger.info("Using cached comparison results from session_id only")
            processing_status[process_id]["tasks"]["compare"] = True
            processing_status[process_id]["tasks"]["understand_cv"] = True
            processing_status[process_id]["tasks"]["understand_offer"] = True
            return cached_results, True, cached_cv_analysis, cached_job_offer_analysis
        else:
            logger.warning(f"Session ID '{session_id}' not found in cache")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "session_not_found",
                    "message": f"Session '{session_id}' was not found in the system.",
                    "suggestion": "Please verify that the session ID is correct or provide CV and job offer files to create a new analysis."
                }
            )

    # If files are provided, proceed with normal flow
    if not cv_text or not job_offer_text:
        raise HTTPException(
            status_code=400,
            detail="Either provide CV and job offer files/links, or provide a valid session_id"
        )

    # Generate hashes for cache lookup
    cv_text_hash = generate_hash(cv_text)
    job_offer_text_hash = generate_hash(job_offer_text)
    additional_considerations_hash = (
        generate_hash(additional_considerations) if additional_considerations else None
    )

    # Check cache if session_id is provided
    if session_id:
        cached_results = await get_cached_comparison(
            session_id,
            cv_text_hash,
            job_offer_text_hash,
            additional_considerations_hash
        )
        if cached_results:
            logger.info("Using cached comparison results")
            processing_status[process_id]["tasks"]["compare"] = True
            # Return cached results, but we still need to analyze for PDF generation
            # Even when using cache, we need cv_analysis and job_offer_analysis for PDF
            return cached_results, True, None, None

    # Compute comparison
    log_task("Compare and generate results")
    processing_status[process_id]["tasks"]["compare"] = True

    cv_analysis, job_offer_analysis = await analyze_documents(
        cv_text, job_offer_text, process_id
    )

    comparison_results = await compare_cv_and_offer(
        cv_analysis,
        job_offer_analysis,
        additional_considerations
    )

    # Save to cache if session_id is provided
    if session_id:
        await save_comparison_to_cache(
            session_id,
            cv_text_hash,
            job_offer_text_hash,
            additional_considerations_hash,
            comparison_results,
            cv_analysis,
            job_offer_analysis
        )

    return comparison_results, False, cv_analysis, job_offer_analysis


async def generate_and_upload_pdf(
    cv_text: str,
    job_offer_text: str,
    comparison_results: dict,
    additional_considerations: str | None,
    process_id: str,
    cv_analysis: str | None = None,
    job_offer_analysis: str | None = None
) -> io.BytesIO:
    """Generate PDF and store in memory for download"""
    # Analyze documents for PDF if not already analyzed
    if not cv_analysis or not job_offer_analysis:
        cv_analysis, job_offer_analysis = await analyze_documents(
            cv_text, job_offer_text, process_id
        )

    log_task("Generate PDF")
    processing_status[process_id]["tasks"]["generate_pdf"] = True

    pdf_buffer = generate_pdf(
        cv_analysis=cv_analysis,
        job_offer_analysis=job_offer_analysis,
        strengths=comparison_results["strengths"],
        weaknesses=comparison_results["weaknesses"],
        recommendation=comparison_results["recommendation"],
        match_percentage=comparison_results["matchPercentage"],
        four_week_plan=comparison_results["fourWeekPlan"],
        additional_considerations=additional_considerations
    )

    return pdf_buffer


@app.post("/api/process")
async def process_application(
    cv_file: UploadFile | None = File(None),
    cv_link: str | None = Form(None),
    job_offer_file: UploadFile | None = File(None),
    job_offer_link: str | None = Form(None),
    job_offer_text: str | None = Form(None),
    additional_considerations: str | None = Form(None),
    user_id: str = Form("demo"),
    session_id: str | None = Form(None),
    user_ip: str | None = Form(None)
):
    """Process CV and job offer to generate analysis"""
    logger.info("Starting process application")
    logger.info(f"User ID: {user_id}, Session ID: {session_id}")

    process_id = f"process_{datetime.now().timestamp()}"
    initialize_process_status(process_id)

    try:
        # Extract text from inputs (only if files/links are provided)
        cv_text = None
        job_offer_text_extracted = None

        if cv_file or cv_link:
            cv_text = await extract_text_from_input(cv_file, cv_link)

        # Prioridad: texto directo > archivo > enlace
        if job_offer_text:
            job_offer_text_extracted = job_offer_text
        elif job_offer_file or job_offer_link:
            job_offer_text_extracted = await extract_text_from_input(job_offer_file, job_offer_link)

        has_files = bool(cv_text or job_offer_text_extracted)

        # Check if session_id exists in cache
        session_exists_in_cache = False
        if session_id:
            cached_results, _, _ = await get_cached_comparison_by_session_id(session_id)
            session_exists_in_cache = cached_results is not None

        # Determine if this is a new request:
        # - If files are provided → New request (processes files, regardless of cache)
        # - If session_id doesn't exist in cache AND files are provided → New session
        # - If session_id exists in cache AND no files → Reusing existing session (not new request)
        is_new_request = has_files

        # If trying to reuse a session that doesn't exist, return error
        if not has_files and session_id and not session_exists_in_cache:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "session_not_found",
                    "message": f"Session '{session_id}' was not found in the system.",
                    "suggestion": "Please verify that the session ID is correct or provide CV and job offer files to create a new analysis."
                }
            )

        # Check global rate limit FIRST (for all new requests)
        if is_new_request:
            total_requests = await count_total_requests(hours=24)
            if total_requests >= 10:
                logger.warning(f"Global rate limit exceeded: {total_requests} total requests in 24 hours")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "global_rate_limit_exceeded",
                        "message": "The global limit of 10 daily queries has been reached.",
                        "suggestion": "Please try again tomorrow. This limit protects the system from potential attacks."
                    }
                )

        # Check per-IP rate limit (only for new requests)
        if is_new_request and user_ip:
            request_count = await count_user_requests(user_ip, hours=24)
            if request_count >= 2:
                logger.warning(f"Rate limit exceeded for IP {user_ip}: {request_count} requests")
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": "You have reached the limit of 2 queries per day.",
                        "suggestion": "Please try again tomorrow or contact the administrator if you need more queries."
                    }
                )

        # If no files and no session_id, return error
        if not has_files and not session_id:
            raise HTTPException(
                status_code=400,
                detail="Either provide CV and job offer files/links, or provide a session_id"
            )

        # Get or compute comparison results
        comparison_results, from_cache, cv_analysis, job_offer_analysis = (
            await get_or_compute_comparison(
                cv_text,
                job_offer_text_extracted,
                additional_considerations,
                session_id,
                process_id
            )
        )

        # Generate PDF if we have analyses (from cache or newly computed)
        # PDF can be generated even without original files if we have cached analyses
        pdf_buffer_data = None
        if cv_analysis and job_offer_analysis:
            # We can generate PDF with cached analyses even without original text files
            pdf_buffer = await generate_and_upload_pdf(
                cv_text or "",  # Use empty string if not available
                job_offer_text_extracted or "",  # Use empty string if not available
                comparison_results,
                additional_considerations,
                process_id,
                cv_analysis,
                job_offer_analysis
            )
            pdf_buffer.seek(0)
            pdf_buffer_data = pdf_buffer.read()
        else:
            logger.info("Skipping PDF generation - no analyses available")
            processing_status[process_id]["tasks"]["generate_pdf"] = True

        # Store PDF buffer in memory for download
        processing_status[process_id]["pdf_buffer"] = pdf_buffer_data

        # Store results
        processing_status[process_id]["results"] = {
            **comparison_results,
            "process_id": process_id,
            "pdf_available": pdf_buffer_data is not None
        }
        processing_status[process_id]["status"] = "completed"

        # Save user IP address ONLY if it's a new request (not reusing existing session)
        if is_new_request:
            await save_user_request(process_id, user_id, user_ip)

        return {
            "process_id": process_id,
            "status": "completed",
            "results": processing_status[process_id]["results"]
        }

    except HTTPException:
        # Re-raise HTTPExceptions (like session_not_found) to preserve status code and detail
        raise
    except Exception as e:
        processing_status[process_id]["status"] = "error"
        processing_status[process_id]["error"] = str(e)
        logger.error(f"Error processing application: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{process_id}")
async def get_status(process_id: str):
    """Get processing status"""
    if process_id not in processing_status:
        raise HTTPException(status_code=404, detail="Process not found")

    status_data = processing_status[process_id].copy()

    # Remove pdf_buffer from response (it's too large and not needed in status)
    # PDF can be downloaded via /api/download endpoint
    if "pdf_buffer" in status_data:
        status_data["pdf_buffer"] = "available" if status_data["pdf_buffer"] else None

    return status_data


@app.get("/api/download/{process_id}")
async def download_pdf(process_id: str):
    """Download generated PDF from memory"""
    if process_id not in processing_status:
        raise HTTPException(status_code=404, detail="Process not found")

    pdf_buffer_data = processing_status[process_id].get("pdf_buffer")
    if not pdf_buffer_data:
        raise HTTPException(status_code=404, detail="PDF not found")

    try:
        return StreamingResponse(
            io.BytesIO(pdf_buffer_data),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=career_analysis_{process_id}.pdf"}
        )
    except Exception as e:
        error_msg = str(e)
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading PDF: {error_msg}"
        )




async def count_total_requests(hours: int = 24) -> int:
    """Count total completed requests in the last N hours (global limit)"""
    try:
        # Use admin client to bypass RLS
        if not supabase_admin:
            logger.warning("supabase_admin not available, cannot count total requests")
            return 0

        # Calculate the time threshold
        threshold_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        # Count all requests in the last N hours
        result = supabase_admin.table("user_requests").select(
            "id"
        ).gte("created_at", threshold_time).execute()

        # Count the number of results
        count = len(result.data) if result.data else 0
        logger.info(f"Total requests in the last {hours} hours: {count}")
        return count
    except Exception as e:
        logger.warning(f"Error counting total requests: {str(e)}")
        # If we can't count, allow the request (fail open)
        return 0


async def count_user_requests(user_ip: str, hours: int = 24) -> int:
    """Count completed requests from an IP address in the last N hours"""
    if not user_ip:
        return 0

    try:
        # Use admin client to bypass RLS
        if not supabase_admin:
            logger.warning("supabase_admin not available, cannot count user requests")
            return 0

        # Calculate the time threshold
        threshold_time = (datetime.now() - timedelta(hours=hours)).isoformat()

        # Count requests from this IP in the last N hours
        result = supabase_admin.table("user_requests").select(
            "id"
        ).eq("ip_address", user_ip).gte("created_at", threshold_time).execute()

        # Count the number of results
        count = len(result.data) if result.data else 0
        logger.info(f"IP {user_ip} has {count} requests in the last {hours} hours")
        return count
    except Exception as e:
        logger.warning(f"Error counting user requests: {str(e)}")
        # If we can't count, allow the request (fail open)
        return 0


async def save_user_request(process_id: str, user_id: str, user_ip: str | None):
    """Save user IP address and request timestamp to database (only if process completed)"""
    if not user_ip:
        return  # Skip if no IP provided

    try:
        # Use admin client to bypass RLS
        if not supabase_admin:
            logger.warning("supabase_admin not available, cannot save user request")
            return

        supabase_admin.table("user_requests").insert({
            "ip_address": user_ip,
            "process_id": process_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }).execute()
        logger.info(f"User request saved: IP={user_ip}, process_id={process_id}")
    except Exception as e:
        logger.warning(f"Error saving user request: {str(e)}")
        # Don't fail the request if IP save fails


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
