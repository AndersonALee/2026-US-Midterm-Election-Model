# 2026 US Midterm Election Model

Interactive seat model for the 2026 US midterms: House, Senate and governors. English / 中文 toggle in the top right.

- Live page: https://andersonalee.github.io/2026-US-Midterm-Election-Model/
- `index.html` is the page. It reads `data.json` (current inputs) and `history.json` (one row per model run, used for the trend charts).
- `model.py` + `pvi.json` (Cook 2026 PVI as House fundamentals) are the model. Run `python3 model.py in.json` to simulate and to write `site/data.json` and `site/history.json`.
- The model runs every Tuesday and Saturday morning (Chicago time); each run refreshes the two JSON files.

Model v2: each seat's probability combines four modules in probit space — institution ratings (FPO, Split Ticket, DDHQ, Cook, VoteHub), polls (own weighted average, Senate/governor only), Polymarket and fundamentals (weights 40/30/15/15; House 60/25/15, poll share capped at 50%); seat totals come from a Gaussian-copula simulation. The page also shows its own rating (Solid ≥95%, Likely 80–95%, Lean 65–80%, Tilt 55–65%, Toss-up 45–55%), separate from Cook's. Not an official forecast.
