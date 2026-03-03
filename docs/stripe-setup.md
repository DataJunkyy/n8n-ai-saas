# Stripe Payment Integration Guide

## Overview

This guide walks you through connecting Stripe to your AI SaaS platform. After setup, new subscribers will automatically get registered, receive an auth token, and be able to use the AI assistants immediately.

## Step 1: Create Stripe Account & Products

1. Go to [stripe.com](https://stripe.com) and create an account
2. Complete identity verification
3. Create two products in **Products > Add product**:

| Product | Price | Billing |
|---------|-------|---------|
| Cosmetic Formulation AI | $9.99/month | Recurring |
| Project Management AI | $9.99/month | Recurring |

## Step 2: Create Payment Links

For each product:

1. Go to **Payment Links > Create payment link**
2. Select the product
3. Under **After payment**, set redirect URL to your landing page with a success message
4. Copy the payment link URL (e.g., `https://buy.stripe.com/xxx`)

## Step 3: Update Landing Page

Edit `landing-page/index.html` and replace the placeholder `href` values:

```html
<!-- Cosmetic product -->
<a href="https://buy.stripe.com/YOUR_COSMETIC_LINK" class="cta-btn">Subscribe Now</a>

<!-- Project product -->
<a href="https://buy.stripe.com/YOUR_PROJECT_LINK" class="cta-btn">Subscribe Now</a>
```

## Step 4: Set Up Stripe Webhook

This is the key automation: when someone subscribes, Stripe sends a webhook to your n8n instance, which creates the user automatically.

### In Stripe Dashboard:

1. Go to **Developers > Webhooks > Add endpoint**
2. Set endpoint URL: `https://YOUR_N8N_DOMAIN/webhook/stripe-subscription`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.deleted`
4. Copy the webhook signing secret (`whsec_...`)

### In n8n:

Create a new workflow "Stripe Subscription Handler" with this flow:

```
Webhook (POST /stripe-subscription)
  → Verify Stripe Signature (Code node)
  → Route by Event Type (Switch node)
    → checkout.session.completed → Call Registration Workflow
    → customer.subscription.deleted → Deactivate User
```

**Verify Stripe Signature** (Code node):
```javascript
const crypto = require('crypto');
const body = $input.first().json.body;
const sig = $input.first().json.headers['stripe-signature'];
const secret = 'whsec_YOUR_SIGNING_SECRET'; // Move to n8n credentials

const elements = sig.split(',');
const timestamp = elements.find(e => e.startsWith('t=')).split('=')[1];
const signature = elements.find(e => e.startsWith('v1=')).split('=')[1];

const payload = `${timestamp}.${JSON.stringify(body)}`;
const expected = crypto.createHmac('sha256', secret).update(payload).digest('hex');

if (expected !== signature) {
  return [{ json: { error: 'Invalid signature' } }];
}

return [{ json: { event: body.type, data: body.data.object } }];
```

**On checkout.session.completed:**
- Extract `customer_email` from the session object
- Determine product type from `line_items` metadata (add `projectType: "cosmetic"` or `projectType: "project"` as metadata on your Stripe products)
- Call the registration endpoint:

```
POST https://YOUR_N8N_DOMAIN/webhook/register-user
Headers: X-Admin-Token: b9cd461c9cd9a90ee16c3dd40f8637e3
Body: { email, plan: "basic", projectType: "cosmetic" }
```

- Send welcome email with auth token + chat UI URL

**On customer.subscription.deleted:**
- Look up user by email in Users tab
- Set `Active` to `FALSE`

## Step 5: Welcome Email

After registration succeeds, send the user their access details. You can use n8n's Send Email node or an email API (SendGrid, Resend, etc.).

Template:
```
Subject: Your AI Assistant is Ready!

Hi {email},

Your {productName} subscription is active! Here's how to get started:

1. Open your AI assistant: {chatUIUrl}
2. Your auth token (already embedded in the link): {authToken}

You get 100 conversations per month. Usage resets on the 1st of each month.

Need help? Reply to this email.
```

## Step 6: GitHub Secrets

Add these secrets to your GitHub repo for CI/CD:

| Secret | Value |
|--------|-------|
| `N8N_API_URL` | `https://princeadarkwah.app.n8n.cloud/api/v1` |
| `N8N_API_KEY` | Your n8n API key |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` from Step 4 |

## Architecture Diagram

```
User clicks "Subscribe" on landing page
  → Stripe Checkout (hosted by Stripe)
  → Payment succeeds
  → Stripe sends webhook to n8n
  → n8n verifies signature
  → n8n calls /register-user
    → Creates Google Spreadsheet for user
    → Adds user to registry
  → n8n sends welcome email with auth token
  → User opens Chat UI link
  → User starts chatting with AI assistant
```

## Testing

1. Use Stripe's test mode (toggle in dashboard)
2. Test card: `4242 4242 4242 4242` (any future date, any CVC)
3. Verify user appears in Users tab of shared spreadsheet
4. Test the auth token works with the AI assistant
5. Test subscription cancellation deactivates the user
