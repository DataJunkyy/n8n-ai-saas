"""Create Users tab in the shared AI Platform spreadsheet via a temp n8n workflow."""

import json
import os
import sys
import time
import urllib.request
import uuid

sys.stdout.reconfigure(encoding="utf-8")

API_KEY = os.environ.get("N8N_API_KEY", "")
BASE = "https://princeadarkwah.app.n8n.cloud"
SHARED_SS = "1IDVVby9y7ccYwi5NRjXCx5HRjao2NJ3KNUKDrv-Y3bI"
SHEETS_CRED = {"id": "qpV1Z8tc0XDqAdRH", "name": "Google Sheets account"}

AUTH_TOKEN = "b9cd461c9cd9a90ee16c3dd40f8637e3"
COSMETIC_SS = "1cLv6rS_YjlTGVGrrpWFt7TMz4el1SOsYwlDmzwOwKXI"
PROJECT_SS = "1FLuoMIZiP-fF_p--9uNhp5b6bRaBIS3QmLHuOU0SSHY"


def n8n_api(method, path, data=None):
    url = f"{BASE}/api/v1{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("X-N8N-API-KEY", API_KEY)
    if body:
        req.add_header("Content-Type", "application/json")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())


def make_http_node(node_id, name, position, method, url, body_data):
    return {
        "parameters": {
            "method": method,
            "url": url,
            "authentication": "predefinedCredentialType",
            "nodeCredentialType": "googleSheetsOAuth2Api",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": json.dumps(body_data),
            "options": {},
        },
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": position,
        "credentials": {"googleSheetsOAuth2Api": SHEETS_CRED},
    }


def main():
    if not API_KEY:
        print("Set N8N_API_KEY environment variable")
        sys.exit(1)

    sheets_base = f"https://sheets.googleapis.com/v4/spreadsheets/{SHARED_SS}"

    # Build the setup workflow
    setup_wf = {
        "name": "Setup: Add Users Tab (temp)",
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "GET",
                    "path": "setup-users-tab-temp",
                    "responseMode": "lastNode",
                    "options": {},
                },
                "id": "su-001",
                "name": "Webhook",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [240, 300],
                "webhookId": str(uuid.uuid4()),
            },
            make_http_node(
                "su-002", "Add Users Tab", [460, 300], "POST",
                f"{sheets_base}:batchUpdate",
                {"requests": [{"addSheet": {"properties": {"title": "Users", "index": 3}}}]},
            ),
            make_http_node(
                "su-003", "Add Headers", [680, 300], "POST",
                f"{sheets_base}/values/Users!A1:I1:append?valueInputOption=RAW",
                {"values": [["AuthToken", "Email", "Plan", "SpreadsheetId", "ProjectType",
                             "ConversationsThisMonth", "ConversationsLimit", "CreatedAt", "Active"]]},
            ),
            make_http_node(
                "su-004", "Add Test Users", [900, 300], "POST",
                f"{sheets_base}/values/Users!A2:I3:append?valueInputOption=RAW",
                {"values": [
                    [AUTH_TOKEN, "prince@test.com", "basic", COSMETIC_SS, "cosmetic", "0", "100", "2026-03-02", "TRUE"],
                    [AUTH_TOKEN, "prince@test.com", "basic", PROJECT_SS, "project", "0", "100", "2026-03-02", "TRUE"],
                ]},
            ),
        ],
        "connections": {
            "Webhook": {"main": [[{"node": "Add Users Tab", "type": "main", "index": 0}]]},
            "Add Users Tab": {"main": [[{"node": "Add Headers", "type": "main", "index": 0}]]},
            "Add Headers": {"main": [[{"node": "Add Test Users", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1"},
    }

    # Create
    result = n8n_api("POST", "/workflows", setup_wf)
    wf_id = result["id"]
    print(f"Created workflow: {wf_id}")

    # Activate
    n8n_api("POST", f"/workflows/{wf_id}/activate")
    print("Activated")

    # Call webhook
    time.sleep(2)
    print("Calling webhook...")
    try:
        req = urllib.request.Request(f"{BASE}/webhook/setup-users-tab-temp", method="GET")
        resp = urllib.request.urlopen(req, timeout=30)
        body = resp.read().decode()
        print(f"Response: {body[:300]}")
        print("Users tab created successfully!")
    except Exception as e:
        err_body = ""
        if hasattr(e, "read"):
            err_body = e.read().decode()[:300]
        print(f"Error: {e}")
        if err_body:
            print(f"Body: {err_body}")

    # Cleanup
    time.sleep(1)
    try:
        n8n_api("POST", f"/workflows/{wf_id}/deactivate")
    except Exception:
        pass
    try:
        n8n_api("DELETE", f"/workflows/{wf_id}")
        print(f"Cleaned up temp workflow {wf_id}")
    except Exception:
        print(f"Note: manually delete workflow {wf_id}")


if __name__ == "__main__":
    main()
