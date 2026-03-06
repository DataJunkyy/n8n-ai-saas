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
   - `GITHUB_ID` and `GITHUB_SECRET` — GitHub OAuth app credentials for NextAuth (optional)
   - `NEXTAUTH_SECRET` — a long random string used by NextAuth to sign cookies
4. Vercel will provide preview URLs for each PR and automatic deployments.

Realtime content edits

- Recommended: connect a headless CMS (Sanity or Contentful) to manage marketing copy and pages.

Next steps

- Add `pages/demo.js` for sandbox onboarding.
- Integrate Auth (Auth0, Clerk, or NextAuth) for protected demo environments.
-
NextAuth setup (quick)

1. Create a GitHub OAuth app (or choose another provider) and set the callback URL to `https://<YOUR_VERCEL_DOMAIN>/api/auth/callback/github`.
2. In Vercel Project Settings → Environment Variables add:
   - `GITHUB_ID` = <your GitHub OAuth client id>
   - `GITHUB_SECRET` = <your GitHub OAuth client secret>
   - `NEXTAUTH_SECRET` = <a long random string>
3. Deploy — users visiting `/demo` will be redirected to sign-in and then see the protected demo.
- Add a short demo video and Calendly scheduling.
