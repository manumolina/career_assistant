# Career Assistant

Web application that helps people identify their strengths and weaknesses when applying for a job offer.

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: Next.js with React and TypeScript
- **Styling**: Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **AI**: Google Gemini API
- **Containerization**: Docker

## Features

- CV and job offer analysis using Gemini AI
- Automatic comparison between CV and job offer
- 4-week improvement plan generation
- PDF generation with results (direct download)
- Session system: reuse previous analyses without reprocessing
- Multiple ways to provide job offer: file, link, or pasted text
- Rate limiting: protection against abuse (2 requests/IP/day, 10 global/day)
- IP tracking for usage control
- 100% responsive interface for PC and mobile

## Setup

### Prerequisites

- Docker and Docker Compose
- Supabase account
- Google Gemini API Key

### 1. Supabase Configuration

1. Create a project in Supabase
2. Run the SQL script in `supabase_schema.sql` to create the tables:
   - `comparison_cache`: Stores comparison results and analyses for session reuse
     - Fields: `session_id`, `cv_text_hash`, `job_offer_text_hash`, `comparison_results`, `cv_analysis`, `job_offer_analysis`
     - Retention: 24 hours
   - `user_requests`: Stores IPs and timestamps of completed requests for rate limiting
     - Fields: `ip_address`, `process_id`, `user_id`, `created_at`
     - Retention: 30 days
   - **Note**: The script disables RLS on `comparison_cache` and `user_requests` to allow operations from the backend.
     If you prefer to keep RLS enabled, comment the corresponding lines and uncomment the alternative policies in the script.

### 2. Environment Variables

Create a `.env` file in the project root:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Gemini API
GEMINI_API_KEY=your_gemini_api_key
# Optional: Specify model name (default: gemini-1.5-flash)
# GEMINI_MODEL=gemini-1.5-flash
```

### 3. Running with Docker

```bash
# Build and run containers
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Running without Docker (Development)

#### Backend

The backend uses Poetry to manage dependencies:

```bash
# Install Poetry (if you don't have it)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
cd backend
poetry install

# Activate virtual environment and run
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or run commands inside Poetry environment
poetry shell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Useful Poetry commands:**
```bash
# Add a new dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Export to requirements.txt (if needed)
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

#### Frontend

```bash
npm install
npm run dev
```

## Project Structure

```
career_assistant/
├── backend/              # FastAPI Backend
│   ├── main.py          # Main application
│   ├── pyproject.toml    # Poetry configuration
│   ├── poetry.lock      # Poetry lock file (generated)
│   ├── lib/             # Application modules
│   │   ├── gemini_client.py
│   │   ├── supabase_client.py
│   │   └── pdf_generator.py
├── app/                  # Next.js Frontend
│   ├── page.tsx         # Main page
│   ├── layout.tsx       # Layout
│   └── globals.css      # Global styles
├── components/           # React Components
│   ├── FileInput.tsx
│   ├── ProgressTracker.tsx
│   └── ResultsDisplay.tsx
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── supabase_schema.sql
```

## Database

The application requires the following tables in Supabase:

### `comparison_cache` Table
Stores comparison results for session reuse:
- `session_id`: TEXT (primary key) - Unique session ID
- `cv_text_hash`: TEXT - Hash of CV text
- `job_offer_text_hash`: TEXT - Hash of job offer text
- `additional_considerations_hash`: TEXT - Hash of additional considerations
- `comparison_results`: JSONB - Comparison results
- `cv_analysis`: TEXT - CV analysis
- `job_offer_analysis`: TEXT - Job offer analysis
- `created_at`: TIMESTAMP - Creation date

### `user_requests` Table
Stores completed requests for rate limiting:
- `id`: SERIAL (primary key)
- `ip_address`: TEXT - User IP address
- `process_id`: TEXT - Process ID
- `user_id`: TEXT - User ID
- `created_at`: TIMESTAMP - Request date

## Rate Limiting

The system implements two levels of protection:

1. **Global limit**: Maximum 10 total requests per day (protects against distributed attacks)
2. **Per-IP limit**: Maximum 2 requests per IP per day (protects against individual abuse)

**Note**: Only requests that process new files (new sessions) are counted. Reusing previous sessions does not count towards these limits.

## Troubleshooting

### Error 404 with Gemini models

If you receive an error `404 models/gemini-... is not found`, you can:

1. **List available models**:
   ```bash
   cd backend
   python list_models.py
   ```

2. **Specify a different model** in your `.env`:
   ```env
   GEMINI_MODEL=gemini-1.5-flash
   ```
   
   Common models:
   - `gemini-1.5-flash` (fast and economical)
   - `gemini-1.5-pro` (more powerful)
   - `gemini-pro` (legacy)

3. **Update Google Generative AI package**:
   ```bash
   pip install --upgrade google-generativeai
   ```

## Automatic Cleanup

### Comparison Cache
Cached results are automatically deleted after 24 hours. You can run the SQL function `delete_old_comparison_cache()` periodically.

### Request Logs
IP logs are automatically deleted after 30 days. You can run the SQL function `delete_old_user_requests()` periodically.

## Usage

### Normal Process (New Session)

1. Access the application at http://localhost:3000
2. **CV**: Upload a file or provide a link to your CV
3. **Job Offer**: Choose one of these options:
   - Upload a file
   - Provide a link
   - **Or paste the content directly** (useful for LinkedIn offers or other sites that require authentication)
4. (Optional) Add additional considerations
5. Click "Start Process"
6. Wait for the analysis to complete
7. Review the results and download the PDF
8. **Save your Session ID**: Copy the current session ID to reuse this analysis later

### Reuse Previous Session

1. Access the application
2. In the "Previous Session ID" field, paste the session ID you saved
3. Click "Start Process"
4. The system will retrieve the previous analysis results without reprocessing
5. You can download the PDF if available

**Note**: You cannot use a previous session and provide files at the same time. Choose one option or the other.

## API Endpoints

- `POST /api/process` - Process CV and job offer
- `GET /api/status/{process_id}` - Get processing status
- `GET /api/download/{process_id}` - Download generated PDF

Complete API documentation available at http://localhost:8000/docs
