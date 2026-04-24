# QuarterWatch

An earnings call intelligence platform. Enter a public company ticker and quarter, and QuarterWatch automatically fetches the earnings call transcript, splits it into named segments (CEO remarks, CFO review, Q&A), and runs a multi-layer analysis pipeline on each one. Results surface on a live React dashboard with segment-level sentiment, confidence and hedging scores, flagged risk language, extracted financial entities, verified summaries, and a historical price movement chart showing how the stock moved after the call.

The pipeline is built to degrade gracefully rather than fail silently. Every stage has a documented fallback, and the UI always tells you the provenance and confidence level of what it is showing.

---

## What it does

**Job submission.** The user enters a ticker and quarter. The backend checks whether a completed job already exists for that pair and returns it immediately if so. Otherwise it creates a new job, queues it via Cloud Tasks, and the frontend polls for status every 3 seconds.

**Transcript fetching.** The worker calls the Financial Modeling Prep API to fetch the transcript. If the API fails or no transcript is found, the job status is set to `awaiting_upload` and the frontend prompts the user to paste the transcript manually. The pipeline resumes from that point with no loss of functionality.

**Segmentation.** A rule-based parser splits the transcript into named sections. If fewer than 2 segments are detected, Gemini is called as a fallback. If that also fails, the full transcript is processed as a single segment named "Full Transcript" and a notice is shown in the dashboard.

**Sentiment scoring.** Each segment is sent to the GCP Natural Language API. Segments under 50 words are skipped and marked `insufficient_data`. Failed API calls are retried up to 3 times with exponential backoff. If all retries fail, the segment is marked `unavailable` and processing continues.

**Confidence and hedging scoring.** Each segment is sent to Vertex AI Gemini with a structured prompt asking for a confidence score and the phrases that drove it, returned as JSON. If the response is malformed, it retries once with a stricter prompt. If that also fails, a keyword heuristic scorer runs instead and the result is flagged `scoring_method: heuristic` so the UI can label it differently.

**Named entity extraction.** The NL API runs first for a general entity pass. Gemini runs second for financial-specific entities. Any entity returned by Gemini that cannot be found as a substring in the original segment text is discarded before storage to prevent hallucinated entities from reaching the database.

**Summarization.** Each segment is sent to Gemini for a structured summary validated against a Pydantic schema. If validation fails, it retries once. If that also fails, an extractive summary is generated from the first and last two sentences of the segment. Extractive results are flagged `summary_method: extractive`.

**Faithfulness verification.** Each generated summary is scored against its source segment. Above 0.8 it is marked verified. Between 0.5 and 0.8, specific claims are flagged in the UI with a warning icon. Below 0.5, a clear warning is shown: "This summary could not be fully verified against the source text." A verification failure never blocks the pipeline.

**Price movement.** A nightly Cloud Scheduler job fetches closing price on the call date, the next day, and one week later from Alpha Vantage. If the ticker is delisted or data is unavailable, the chart shows a label rather than a zero or a wrong number.

---

## Failure handling

| Stage | Failure | What happens |
|---|---|---|
| Transcript fetch | API down or transcript not found | Job set to `awaiting_upload`, user prompted to paste manually |
| Segmentation (rule-based) | Fewer than 2 segments | Gemini segmentation fallback |
| Segmentation (Gemini) | Also fails | Process as "Full Transcript", notice shown in UI |
| Sentiment | API error | Retry 3x with exponential backoff. If all fail, mark `unavailable` |
| Sentiment | Segment under 50 words | Mark `insufficient_data`, skip |
| Confidence scoring | Malformed JSON from Gemini | Retry with stricter prompt. If still fails, keyword heuristic, flag `heuristic` |
| Entity extraction (NL API) | API failure | Skip NL API pass, use Gemini output only |
| Entity extraction | Gemini entity not in source text | Discard before storage |
| Entity extraction | Both APIs fail | Store empty list, continue |
| Summarization | Invalid JSON or schema mismatch | Retry once. If still fails, extractive fallback, flag `extractive` |
| Faithfulness check | Gemini errors or score below threshold | Mark `unverified`, surface warning in UI, never block pipeline |
| Cloud Tasks | Queue unreachable | Job set to `failed`, error returned to frontend immediately |
| Price fetch | No data or delisted ticker | Mark fields `unavailable`, show label in UI |

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS, Recharts |
| Backend API | FastAPI, Python, SQLAlchemy, Alembic |
| Worker | Python, Cloud Run |
| Database | PostgreSQL on Cloud SQL |
| Task queue | Cloud Tasks |
| Storage | Cloud Storage |
| Scheduler | Cloud Scheduler |
| AI / ML | GCP Natural Language API, Vertex AI Gemini |
| Infrastructure | Terraform |
| CI / CD | GitHub Actions |
| Auth | NextAuth.js (Google OAuth + password login) |
| External APIs | Financial Modeling Prep, Alpha Vantage |

---

## Project structure

```
quarterwatch/
├── frontend/
│   ├── pages/
│   ├── components/
│   └── hooks/
├── backend/
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── worker/
│       ├── segmenter.py
│       ├── sentiment.py
│       ├── confidence.py
│       ├── entities.py
│       ├── summarizer.py
│       └── faithfulness.py
├── infra/
│   ├── main.tf
│   └── scripts/
├── docs/
└── docker-compose.yml
```

---

## API reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/jobs` | Submit a new analysis job |
| `GET` | `/api/jobs/{job_id}/status` | Poll job status |
| `PUT` | `/api/jobs/{job_id}/transcript` | Upload transcript manually |
| `GET` | `/api/jobs/{job_id}/results` | Fetch full results |
| `GET` | `/api/jobs` | List all jobs for the current user |

---

## Database schema

Key tables:

- `users` — accounts supporting password login and Google OAuth
- `jobs` — one row per ticker and quarter, tracks pipeline status
- `segments` — one row per named segment within a transcript
- `sentiment_results` — NL API output per segment with availability flag
- `confidence_results` — Gemini scores per segment with scoring method flag
- `entities` — extracted financial entities after hallucination filtering
- `summaries` — generated summaries with faithfulness scores and verification status
- `price_data` — closing price on call date, D+1, and D+7

---

## Architecture diagram

An interactive system architecture diagram is published at: **[your-username.github.io/quarterwatch](https://dixisouls.github.io/quarterwatch)**