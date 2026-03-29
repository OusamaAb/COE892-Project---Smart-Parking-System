# Smart Parking System

## Prerequisites

- Python 3.10+
- Node.js 18+

## Backend Setup

```bash
cd smart-parking-system/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python start_services.py
```

On first run, **SQLite** files are created next to each data-owning service:

- `backend/parking_service/parking.db` — spots (seeded once if empty)
- `backend/reservation_service/reservations.db` — reservations

Delete a `.db` file to reset that service’s data (parking will re-seed).

**Lot clock** (reservation service): simulated time starts at **9:00 AM** each run and is **not** saved to disk. Every **60 seconds** of real time, the lot clock advances **15 minutes**. New reservations store a leave-by time on that clock; when time is up, spots are freed automatically.

## Frontend Setup

Open a second terminal:

```bash
cd smart-parking-system/frontend
cp vite.config.example.js vite.config.js   # first clone only, if vite.config.js is missing
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

## GitHub Pages (static frontend)

Publishing **“from branch / root”** only serves files at the repo root (mostly `README.md`), not the Vite app. Use **GitHub Actions** instead:

1. Repo **Settings → Pages → Build and deployment**: set **Source** to **GitHub Actions** (not “Deploy from a branch”).
2. Push to `main` (or run the **Deploy frontend to GitHub Pages** workflow manually). The workflow builds `frontend/` and deploys `dist/`.
3. Site URL: `https://<your-username>.github.io/COE892-Project---Smart-Parking-System/` (repo name must match your repository).

The gateway is not on Pages. For a public demo, run the backend locally (or on a server) and expose it with HTTPS (e.g. a tunnel). Add a repository variable **`VITE_API_BASE_URL`** (Settings → Secrets and variables → Actions → Variables) with that gateway URL (no trailing slash), then rebuild Pages so the built JS points at it.
