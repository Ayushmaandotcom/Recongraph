# Deploying ReconGraph

Two independent deploys: the Next.js dashboard (Vercel) and the FastAPI backend (Render). The UI works standalone in demo mode even if you skip the API deploy — it falls back to the pre-baked demo_results.json — so if you only have time for one, do the UI.

## 1. Deploy the UI to Vercel (~5 minutes)

Install the CLI and log in:
```bash
npm install -g vercel
vercel login
```

From the repo root:
```bash
cd recongraph-ui
vercel
```

When prompted:
- "Set up and deploy?" → Yes
- "Link to existing project?" → No (first time)
- Root directory → confirm `recongraph-ui` (should auto-detect since you cd'd in)
- Framework preset → Next.js (auto-detected)

Vercel will build and give you a `https://<project>.vercel.app` URL. That's your live demo link — this is what goes on your resume and in the README.

For subsequent deploys after changes: `vercel --prod`.

**Optional — wire it to a live backend instead of just the static demo:**
In the Vercel dashboard → Project → Settings → Environment Variables, add `NEXT_PUBLIC_API_URL` = the Render URL from step 2 below, then redeploy. If you skip this, the "Load Demo Dataset" button still works via the static JSON fallback — nothing breaks either way.

## 2. Deploy the API to Render (~5 minutes)

Push `render.yaml` (repo root) to your GitHub repo — it's already written for you in this delivery.
Go to [render.com](https://render.com/) → New → Blueprint → connect the Ayushmaandotcom/Recongraph repo → Render reads `render.yaml` automatically.
Click Apply. First deploy takes a few minutes (installs recongraph + FastAPI). Render's free tier spins down after 15 min idle and takes ~30-60s to wake back up on the next request — fine for a portfolio demo, worth mentioning if you demo it live so a cold start doesn't look broken.

Copy the resulting `https://recongraph-api.onrender.com`-style URL and (if you want the live backend, not just static demo) set it as `NEXT_PUBLIC_API_URL` in Vercel per step 1.

## 3. After both are live

Update the README's "Live Demo" line (already added in this delivery — just fill in your actual URLs) so anyone opening the repo sees a clickable link before they see a single line of code.

### Known limitation to be upfront about in interviews

The dashboard's real CSV upload inputs are currently placeholders ("Coming Soon" in UploadScreen.tsx) — only the pre-computed demo dataset is wired into the UI today, even though the API's `/reconcile` endpoint already accepts arbitrary CSV uploads. If you want the full loop live before showing this around, wiring UploadScreen to POST `/reconcile` with two file inputs and polling `/runs/{run_id}` is the natural next step — happy to build that next if you want it done before you deploy.
