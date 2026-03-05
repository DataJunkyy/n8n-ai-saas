# RxServicesSolutions — Starter Site

This repository is a minimal Next.js starter for the RxServicesSolutions marketing site and sandbox.

Quick start

```bash
# install
npm install
# dev server
npm run dev
```

Deploy to Vercel

1. Create a new Git repo and push this code.
2. Sign in to Vercel and import the repository.
3. Set environment variables in Vercel:
   - `NEXT_PUBLIC_GA_ID` — Google Analytics Measurement ID (optional)
4. Vercel will provide preview URLs for each PR and automatic deployments.

Realtime content edits

- Recommended: connect a headless CMS (Sanity or Contentful) to manage marketing copy and pages.

Next steps

- Add `pages/demo.js` for sandbox onboarding.
- Integrate Auth (Auth0 or Clerk) for protected demo environments.
- Add a short demo video and Calendly scheduling.
