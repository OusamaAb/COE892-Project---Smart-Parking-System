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
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.
