# Sharing the SEC Plot GUI

## Quick short-term: share a zip

1. **Zip the project** (from the parent of `Protein Raman`):
   - Include: `app.py`, `plot_sec_to_svg.py`, `sec_plot_gui.html`, `requirements.txt`, `RUN_GUI.md`, and the `Atkinson_Hyperlegible` folder (optional; plots work without it, but fonts will fall back to system defaults).
   - Exclude: `Final SEC figures /`, `SEC_figures_SVG/`, and any `__pycache__` or `.pyc` files.

2. **Recipients**:
   - Install Python 3.8+.
   - Unzip, then:
     ```bash
     cd "Protein Raman"
     pip install -r requirements.txt
     python app.py
     ```
   - Open **http://127.0.0.1:5000** in a browser.

**Even quicker:** You run `python app.py` on your machine and use **[ngrok](https://ngrok.com)** so others can reach it temporarily:
- Install ngrok, then run: `ngrok http 5000`
- Share the generated HTTPS URL (e.g. `https://abc123.ngrok.io`). No zip, no install for them; your app must stay running and your machine on.

---

## Hosting somewhere (public URL)

So others can use it without installing anything:

| Option | Effort | Notes |
|--------|--------|--------|
| **Render** | Low | Connect a GitHub repo; free tier, sleeps after inactivity. |
| **PythonAnywhere** | Low | Upload project or clone from GitHub; free tier has limits. |
| **Railway / Fly.io** | Medium | Free tiers; deploy via GitHub or CLI. |

**Important for hosting:**
- **Fonts**: The app looks for `Atkinson_Hyperlegible/` next to the script. Either include that folder in the repo (if the license allows) or make font loading optional so the app still runs without it (it already does: if the folder is missing, matplotlib uses defaults).
- **File size**: Large CSV uploads may hit request size limits on free tiers; keep CSVs reasonable or document the limit.

**Minimal Render setup (once you have a GitHub repo):**
1. [Render](https://render.com) → New → Web Service.
2. Connect the repo. **Build**: `pip install -r requirements.txt`. **Start**: `gunicorn app:app`.
3. Deploy. Render gives you a URL like `https://your-app.onrender.com`.

---

## Proper “GitHub way” (repo + optional deploy)

1. **Create a repo** (e.g. `sec-plot-gui` or `protein-raman-sec`).

2. **Repo layout** (minimal):
   ```
   sec-plot-gui/
   ├── .gitignore
   ├── README.md
   ├── RUN_GUI.md
   ├── SHARING.md
   ├── requirements.txt
   ├── app.py
   ├── plot_sec_to_svg.py
   ├── sec_plot_gui.html
   └── Atkinson_Hyperlegible/   # optional; add if license allows, or document where to get it
   ```

3. **.gitignore** (so you don’t commit data or caches):
   ```
   __pycache__/
   *.pyc
   Final SEC figures /
   SEC_figures_SVG/
   .env
   ```

4. **README.md** in the repo:
   - One-line description: “Web GUI to turn SEC CSV data into Arcadia-styled SVG plots.”
   - “Quick start”: clone, `pip install -r requirements.txt`, `python app.py`, open http://127.0.0.1:5000.
   - Link to `RUN_GUI.md` for full GUI instructions and `SHARING.md` for sharing/hosting.

5. **Optional: runnable from the repo root**  
   Make sure paths work when run from repo root (your code already uses `Path(__file__).resolve().parent`, so running `python app.py` from the repo root is enough).

6. **Optional: Docker**  
   Add a `Dockerfile` so anyone can run:
   ```bash
   docker build -t sec-plot-gui .
   docker run -p 5000:5000 sec-plot-gui
   ```
   Then open http://localhost:5000.

7. **Deploy from GitHub**  
   Connect the repo to Render (or PythonAnywhere, Railway, Fly.io) and point the service at `app:app` with the same dependencies so the hosted app is always in sync with the repo.

---

## Summary

| Goal | Approach |
|------|----------|
| **Quick, no install for others** | You run `python app.py` + ngrok; share the ngrok URL. |
| **Others run it themselves, minimal setup** | Zip project + RUN_GUI.md; they install deps and run `python app.py`. |
| **Public URL you maintain** | Put code on GitHub, connect to Render (or similar), add gunicorn and deploy. |
| **Long-term, proper** | GitHub repo + README + .gitignore, optional Docker, then deploy from the same repo. |
