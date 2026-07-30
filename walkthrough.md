
## Track B (UI) Completion

The Reconciliation Review Dashboard has been scaffolded and implemented.

### Setup & Architecture
1. **recongraph-api (FastAPI)**
   - Houses the `ReconGraphEngine` interface to the web world.
   - Provides `/reconcile` for CSV uploads and `/demo` to instantly serve the challenge dataset.
2. **recongraph-ui (Next.js 15, Tailwind v4)**
   - Built with strict adherence to the "missing-vs-contradictory" thesis.
   - Defaults to a "Financial Intelligence" deep slate dark mode theme with vibrant blue (`#3b82f6`) and amber/red conflict indicators.
   - **Static Demo Fallback**: As requested, the challenge dataset result is pre-baked as `demo_results.json` into the `public/` directory for instant Vercel rendering.

### The Screens
- **Screen 1 (Upload & Run)**: Greets the user with "Reconcile with Confidence." and offers a one-click "Load Demo Dataset" button.
- **Screen 2 (Results Dashboard)**: Displays the `Strict Conservation` indicator prominently ensuring zero data loss, along with match rate metrics.
- **Screen 3 (Review Queue)**: A filterable table categorizing packets into Ambiguous, Weak Evidence, and Leftovers.
- **Screen 4 (Packet Detail)**: The core thesis implementation. Side-by-side display of internal purchases vs counterparty GST records. It maps the engine's `SemanticFindings` (e.g. `AMOUNT_MULTIPLE`, `DISTINCT_EVENT_IDENTITY_EVIDENCE`) to distinct, colored alert boxes (Grey for unknown, Red for conflicts) based directly on the deterministic engine's `ReviewPacket.explanation` and `headline`.

### Validation
Run the UI locally to verify:
```bash
cd recongraph-ui
npm run dev
```

Please review the UI milestone branch (`feature/ui`). If it meets your expectations, we can merge to `main` and proceed to Track C (Release).
