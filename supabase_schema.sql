-- Create comparison_cache table to store comparison results
CREATE TABLE IF NOT EXISTS comparison_cache (
    session_id TEXT PRIMARY KEY,
    cv_text_hash TEXT NOT NULL,
    job_offer_text_hash TEXT NOT NULL,
    additional_considerations_hash TEXT,
    comparison_results JSONB NOT NULL,
    cv_analysis TEXT,
    job_offer_analysis TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on hashes for faster lookups
CREATE INDEX IF NOT EXISTS idx_comparison_cache_hashes 
    ON comparison_cache(cv_text_hash, job_offer_text_hash, additional_considerations_hash);

-- Create index on created_at for cleanup
CREATE INDEX IF NOT EXISTS idx_comparison_cache_created_at ON comparison_cache(created_at);

-- Function to clean up old cache entries (older than 24 hours)
CREATE OR REPLACE FUNCTION delete_old_comparison_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM comparison_cache
    WHERE created_at < NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- Disable RLS on comparison_cache table (or configure policies)
-- Option 1: Disable RLS (simpler, but less secure)
ALTER TABLE comparison_cache DISABLE ROW LEVEL SECURITY;

-- Option 2: Enable RLS with permissive policy (if you want to keep RLS enabled)
-- ALTER TABLE comparison_cache ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Allow all operations on comparison_cache" ON comparison_cache
--     FOR ALL
--     USING (true)
--     WITH CHECK (true);

-- Create user_requests table to track IP addresses and request timestamps
CREATE TABLE IF NOT EXISTS user_requests (
    id SERIAL PRIMARY KEY,
    ip_address TEXT NOT NULL,
    process_id TEXT,
    user_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on ip_address for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_requests_ip ON user_requests(ip_address);

-- Create index on created_at for cleanup and rate limiting queries
CREATE INDEX IF NOT EXISTS idx_user_requests_created_at ON user_requests(created_at);

-- Disable RLS on user_requests table (or configure policies)
ALTER TABLE user_requests DISABLE ROW LEVEL SECURITY;

-- Function to clean up old request entries (older than 30 days)
CREATE OR REPLACE FUNCTION delete_old_user_requests()
RETURNS void AS $$
BEGIN
    DELETE FROM user_requests
    WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

