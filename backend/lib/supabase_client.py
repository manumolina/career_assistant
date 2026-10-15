import os
import socket
from urllib.parse import urlparse

from supabase import Client, create_client

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase credentials not found in environment variables")

supabase_client: Client = create_client(supabase_url, supabase_key)
supabase_admin: Client = create_client(supabase_url, supabase_service_key) if supabase_service_key else supabase_client


def check_supabase_connection() -> dict:
    """Verify Supabase DNS resolution and database connectivity."""
    hostname = urlparse(supabase_url).hostname if supabase_url else None
    result = {
        "url_configured": bool(supabase_url),
        "anon_key_configured": bool(supabase_key),
        "service_key_configured": bool(supabase_service_key),
        "hostname": hostname,
        "dns_resolves": False,
        "reachable": False,
        "error": None,
    }

    if not hostname:
        result["error"] = "SUPABASE_URL is missing or invalid"
        return result

    try:
        socket.getaddrinfo(hostname, 443)
        result["dns_resolves"] = True
    except socket.gaierror as e:
        result["error"] = f"DNS resolution failed: {e}"
        return result

    try:
        client = supabase_admin if supabase_service_key else supabase_client
        client.table("comparison_cache").select("session_id").limit(1).execute()
        result["reachable"] = True
    except Exception as e:
        result["error"] = str(e)

    return result
