# LUNARIS v3.3 — Lumi dock navigation

- Adds a seventh bottom-navigation item, **Lumi**, after Impact.
- Clicking Lumi opens the existing Lumi assistant on the Today page, scrolls it into view and focuses its question input.
- Keeps the Action Atlas tab, all existing routes, and the current bounded local Lumi guide intact.
- Does **not** add Groq integration or require an API key. The Groq backend can be integrated later without changing this navigation.

## Codex deployment
Merge the `dist/app/index.html`, `dist/app/app.js`, and `dist/app/styles.css` changes into your current production repository, preserving any newer changes. Verify the seven-item dock on mobile and desktop and that clicking Lumi focuses the chat field. Push to GitHub to trigger Vercel redeployment.
