# LUNARIS COP31 v5 — Integrated Homepage & Feature Architecture

## Architecture
- Preserves the existing COP31 v4 Action & Resilience Lab, Action Atlas and all existing calculators.
- Updates public homepage hero, editorial summary to ten cards, COP31 spotlight and a six-feature editorial connector before the scrolling Dubai story.
- Exposes **Carbon & Cost Wallet** at `/app/wallet/` with its own 8th bottom navigation entry.
- Exposes **Climate Insurance Guide** at `/app/insurance/` with a separate homepage card and Explore entry.
- Connects **Fridge Brain** through FoodPrint in `/app/#choices` with a dedicated `/app/foodprint-fridge/` tool page.
- Connects **Home Resilience** through WattFlow in `/app/#choices` with a dedicated `/app/home-resilience/` tool page.
- Keeps the multilingual construction-worker concept in `/app/cop31-lab/#workers`, built on HeatShield's foundation.
- Keeps the COP31 walkthrough and modeling prototype in `/app/cop31-lab/`.
- No Groq model key or generative Lumi backend is implied or bundled.

## Deployment
Merge files into the COP31 repository ONLY. Keep the frozen Veritas repository and deployment untouched. Static URLs should be deployed with clean nested index.html routing. Preserve production backend/API environment variables and custom Vercel routing. Verify all buttons, calculators, 8-tab mobile dock, and homepage scroll on real devices.

## Science and claims
All wallet transport emission factors are UK proxy assumptions, not Dubai route measurements. Home resilience is a self-report checklist, not camera AI or an engineering inspection. Fridge Brain is date and ingredient rule-based planning, not a food-safety evaluation. Insurance tool is education, not quoted or verified policies. Action Atlas still contains proposals and illustrative scenario assumptions, not measured cooling or independently confirmed projects. Worker feature covers seasonal rule explanation and does not send SMS.
