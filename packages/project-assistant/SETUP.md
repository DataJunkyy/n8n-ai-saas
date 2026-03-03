# AI Project Management Assistant — Setup Checklist

Complete these steps after importing the workflow JSON files into your n8n instance.

## 1. Create Required Credentials

- [ ] **Google Sheets OAuth2** — Connect your Google account
  - Go to n8n Settings → Credentials → Add Credential → Google Sheets
  - After connecting, note the credential ID from the URL

- [ ] **Anthropic API** — Add your Anthropic API key
  - Go to n8n Settings → Credentials → Add Credential → Anthropic
  - Paste your API key from console.anthropic.com

- [ ] **Google Docs OAuth2** — Connect your Google account

## 2. Update Credential IDs in Workflows

After creating credentials, update the placeholder IDs in each workflow:

1. Open each workflow in the n8n editor
2. Click on nodes with a warning icon (missing credentials)
3. Select your credential from the dropdown
4. Save the workflow

## 3. Create Your Spreadsheet

Option A: Import the included `setup-spreadsheet.json` workflow and run it once.

Option B: Manually create a Google Sheet with the required tabs and headers
(see README for schema details).

After creating the spreadsheet, update `YOUR_PROJECT_SPREADSHEET_ID` in all workflows.

## 4. Set Auth Token

Generate a random token for webhook authentication:
```bash
openssl rand -hex 16
```

Replace `YOUR_AUTH_TOKEN` in all workflow Code/IF nodes and Chat UI HTML.

## 5. Activate and Test

1. Activate all workflows (toggle ON in the workflow list)
2. Test with curl:
```bash
curl -X POST https://YOUR_N8N_INSTANCE.app.n8n.cloud/webhook/project-assistant \
  -H 'Content-Type: application/json' \
  -H 'X-Auth-Token: YOUR_AUTH_TOKEN' \
  -d '{"message": "hello"}'
```
