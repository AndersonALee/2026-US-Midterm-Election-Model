# 2026 US Midterm Election Model

Interactive seat model for the 2026 US midterms: House, Senate and governors.

- Live page: https://zhirun-blip.github.io/2026-US-Midterm-Election-Model/ (enable GitHub Pages: Settings > Pages > Deploy from a branch > main / root)
- `index.html` is the page; it reads `data.json` in the same folder.
- `update_site.py` refreshes `data.json` from one model run (run twice a week by a scheduled task) and appends the run to the history shown in the trend chart.

Each seat's probability is a weighted average of four signals (FPO, Polymarket, Cook ratings, fundamentals); seat totals come from a Gaussian-copula simulation. Not an official forecast.
