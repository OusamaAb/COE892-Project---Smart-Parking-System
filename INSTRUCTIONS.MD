# Smart Parking System — how to run it

Paths below assume you are in the **`smart-parking-system`** folder at the root of this repo (the one that contains `backend/` and `frontend/`).

---

## Prerequisites

- **Python** 3.10+
- **Node.js** 18+ (GitHub Actions uses 22 for builds)
- For a **public demo** (GitHub Pages + your laptop): **cloudflared** ([install](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)) — on macOS: `brew install cloudflare/cloudflare/cloudflared`

---

## 1. Local development (frontend + backend on your machine)

### Backend (terminal 1)

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python start_services.py
```

This starts the gateway on **http://localhost:8000** and the other services on 8001–8004.

**Data:** SQLite files appear beside the services (`parking_service/parking.db`, `reservation_service/reservations.db`). Delete a `.db` to reset that part of the system.

### Frontend (terminal 2)

```bash
cd frontend
cp vite.config.example.js vite.config.js    # first time only, if vite.config.js is missing
npm install                                   # first time (or after dependency changes)
npm run dev
```

Open **http://localhost:5173**. The UI talks to the gateway at **http://localhost:8000** by default.

---

## 2. Public demo: GitHub Pages + Cloudflare Tunnel

Visitors open your **GitHub Pages** URL. Their browser loads the static site from GitHub; **API calls** go through an **HTTPS tunnel** to port **8000** on your laptop (while you keep the backend and tunnel running).

### 2a — One-time GitHub setup

1. **Pages:** Repo **Settings → Pages → Build and deployment** → set **Source** to **GitHub Actions** (not “Deploy from a branch”).
2. **Variable for the API:** **Settings → Secrets and variables → Actions → Variables** → create **`VITE_API_BASE_URL`** = your tunnel’s HTTPS URL with **no trailing slash** (you will paste this after you start the tunnel in §2c).
3. After you set or change that variable, run **Actions → Deploy frontend to GitHub Pages → Run workflow** so the site rebuilds with the new API URL.

Your Pages URL looks like:

`https://<your-github-username>.github.io/COE892-Project---Smart-Parking-System/`

(Use your real username and repo name if they differ.)

### 2b — Start the backend with CORS for Pages

The browser’s origin on project Pages is **`https://<username>.github.io`** (not the repo path). The gateway must allow it.

In **terminal 1** (from `backend/`, venv activated):

```bash
export GATEWAY_CORS_ORIGINS=https://YOUR_USERNAME.github.io
python start_services.py
```

Use your real GitHub username. To allow local Vite and Pages together:

```bash
export GATEWAY_CORS_ORIGINS=http://localhost:5173,https://YOUR_USERNAME.github.io
```

### 2c — Cloudflare quick tunnel (HTTPS → gateway)

In **terminal 2** (any directory), with the backend already running:

```bash
cloudflared tunnel --url http://localhost:8000
```

In the output, copy the **`https://….trycloudflare.com`** URL (no trailing slash).

1. Set repo variable **`VITE_API_BASE_URL`** to that value (§2a).
2. Re-run the **Deploy frontend to GitHub Pages** workflow if you changed the URL.

**Note:** A **quick** tunnel gets a **new hostname** each time you restart `cloudflared`. If the URL changes, update **`VITE_API_BASE_URL`** and redeploy Pages again. For a stable hostname you need a **named tunnel** and a domain on Cloudflare (see Cloudflare’s docs).

### 2d — While people use the public site

Keep all of this running on your laptop:

- **`python start_services.py`** (with **`GATEWAY_CORS_ORIGINS`** set as in §2b)
- **`cloudflared tunnel --url http://localhost:8000`**
- Laptop **online** and **not asleep**

Share only the **GitHub Pages** link unless you want them to hit the API directly.

---

## 3. Quick checklist (demo day)

| Step | Action |
|------|--------|
| 1 | `cd backend` → venv on → `export GATEWAY_CORS_ORIGINS=…` → `python start_services.py` |
| 2 | `cloudflared tunnel --url http://localhost:8000` → copy HTTPS URL |
| 3 | GitHub variable **`VITE_API_BASE_URL`** = that URL → run Pages deploy workflow if it changed |
| 4 | Open your **github.io** project URL and test (hard refresh if you just redeployed) |

If the page is blank, check the browser **Console** and **Network** tab; confirm the main **`.js`** asset returns **200** and there are no CORS errors on API calls.

---

## 4. How CI builds the frontend (FYI)

`vite.config.js` is gitignored locally. The **Deploy frontend to GitHub Pages** workflow copies **`vite.config.example.js`** to **`vite.config.js`** before `vite build`, so the React plugin is always used on GitHub. You do not need to commit your local `vite.config.js` for Pages to work.
