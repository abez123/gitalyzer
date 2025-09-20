# Gitalyzer

Gitalyzer is a lightweight web application that turns any public GitHub repository into a
friendly story for non-technical audiences. Paste a repository URL, optionally provide an
OpenAI API key, and receive:

- ✅ A clear written explanation of what the code base does, why it matters, and how to try it.
- ✅ A slide-like presentation mode you can walk through with stakeholders.
- ✅ A polished PDF report that can be downloaded and shared.

The backend is powered by FastAPI and talks to the GitHub API and (optionally) OpenAI. The
frontend is a single-page app built with vanilla HTML, CSS, and JavaScript.

## Features

- **Automatic GitHub discovery** – collects repository metadata, language statistics, recent
  commits, and README excerpts.
- **AI assisted narration** – sends a structured prompt to OpenAI (when an API key is provided)
  using a carefully crafted system prompt so the explanation is approachable to non-developers.
- **Graceful fallback** – if no API key is supplied, the server still produces a generic summary so
  the workflow keeps functioning.
- **Presentation overlay** – transforms the analysis into a set of slides you can present directly
  in the browser.
- **PDF export** – builds a branded PDF using `fpdf2`, ready for offline sharing.

## Getting started

### 1. Install dependencies

Create and activate a virtual environment if you like, then install the Python dependencies:

```bash
pip install -r requirements.txt
```

### 2. Run the development server

Start FastAPI with Uvicorn. It will serve both the API under `/api` and the static frontend from
`frontend/`.

```bash
uvicorn backend.main:app --reload
```

Visit <http://localhost:8000> to open the interface.

### 3. Provide your OpenAI API key (optional but recommended)

Paste your API key into the form when running analyses, or set it as an environment variable and
add a small tweak to the request payload on the frontend if you prefer. The key is forwarded only to
OpenAI for the active request and never stored on the server.

> **Tip:** You can override the OpenAI model by filling in the “Model override” field. By default the
> app uses `gpt-4o-mini` for a balance between speed and quality.

## Project structure

```
backend/
  __init__.py
  ai_agent.py         # Builds the prompts and talks to OpenAI
  config.py           # System prompt and schema definition
  github_client.py    # Fetches repository information from the GitHub API
  main.py             # FastAPI application (serves API + static frontend)
  pdf_generator.py    # Turns analyses into downloadable PDFs
frontend/
  index.html          # Single-page interface
  styles.css          # Custom styles for the dashboard + presentation
  app.js              # Client-side logic for calling the API and rendering results
requirements.txt      # Python dependencies
```

## API overview

The backend exposes a few HTTP endpoints under the `/api` prefix:

- `POST /api/analyze` – accepts `{"repo_url": "https://github.com/owner/name", "api_key": "..."}`
  and returns structured analysis plus the repository snapshot.
- `POST /api/generate-pdf` – accepts the repository name and the structured analysis and returns a
  PDF stream.
- `GET /api/analysis-schema` – returns the human-readable description of each field in the analysis
  payload. Handy if you want to build your own client.

Both endpoints are wired up in the frontend, but you can also call them directly from other tools.

## Notes and limitations

- The application uses GitHub's unauthenticated API which has low rate limits. For heavier use you
  may want to extend the backend to accept a GitHub token.
- The OpenAI integration requires outbound internet access and a valid API key. When the key is
  missing or the request fails, Gitalyzer falls back to a rule-based explanation.
- PDF generation uses standard system fonts for portability. You can customise the styling inside
  `backend/pdf_generator.py`.

## License

This project is provided as-is for demonstration purposes. Feel free to adapt it for your own
workflow.
