"""
Add multi-tenant support to n8n workflows.

Transforms:
1. Main agent workflows: Replace Auth Check IF with User Lookup + adds spreadsheetId
   to all toolWorkflow nodes.
2. Tool sub-workflows: Replace hardcoded spreadsheet IDs with dynamic expression
   referencing Parse Input's spreadsheetId field.

Usage:
    python tools/add-multi-tenant.py [--dry-run]

Modifies files in-place in the workflows/ directory.
"""

import json
import os
import re
import sys
import uuid

sys.stdout.reconfigure(encoding="utf-8")

# Known hardcoded spreadsheet IDs per project
COSMETIC_SPREADSHEET_ID = "1cLv6rS_YjlTGVGrrpWFt7TMz4el1SOsYwlDmzwOwKXI"
PROJECT_SPREADSHEET_ID = "1FLuoMIZiP-fF_p--9uNhp5b6bRaBIS3QmLHuOU0SSHY"
SHARED_SPREADSHEET_ID = "1IDVVby9y7ccYwi5NRjXCx5HRjao2NJ3KNUKDrv-Y3bI"

# Dynamic expression to use instead
SPREADSHEET_EXPR = "={{ $('Parse Input').first().json.spreadsheetId }}"

# Tool sub-workflows that need the spreadsheet ID replaced
COSMETIC_TOOLS = [
    "workflows/tool-create-formula.json",
    "workflows/tool-list-formulas.json",
    "workflows/tool-get-formula-details.json",
    "workflows/tool-manage-ingredient.json",
    "workflows/tool-update-formula.json",
    "workflows/tool-search-ingredients.json",
]

PROJECT_TOOLS = [
    "workflows/tool-list-tasks.json",
    "workflows/tool-manage-task.json",
    "workflows/tool-create-document.json",
    "workflows/tool-get-project-summary.json",
]

MAIN_WORKFLOWS = {
    "workflows/cosmetic-assistant-main.json": COSMETIC_SPREADSHEET_ID,
    "workflows/project-assistant-main.json": PROJECT_SPREADSHEET_ID,
}


def update_tool_workflow(filepath, old_spreadsheet_id):
    """Replace hardcoded spreadsheet ID with dynamic expression in a tool sub-workflow."""
    with open(filepath, "r", encoding="utf-8") as f:
        wf = json.load(f)

    changes = 0

    for node in wf.get("nodes", []):
        params = node.get("parameters", {})

        # Update Google Sheets nodes
        if node.get("type") == "n8n-nodes-base.googleSheets":
            doc_id = params.get("documentId", {})
            if isinstance(doc_id, dict) and doc_id.get("value") == old_spreadsheet_id:
                doc_id["value"] = SPREADSHEET_EXPR
                changes += 1

    return wf, changes


def add_spreadsheet_to_tool_inputs(wf, spreadsheet_source_node="Enrich Prompt"):
    """Add spreadsheetId field to all toolWorkflow nodes' workflowInputs."""
    changes = 0

    for node in wf.get("nodes", []):
        if node.get("type") == "@n8n/n8n-nodes-langchain.toolWorkflow":
            params = node.get("parameters", {})
            inputs = params.get("workflowInputs", {})
            value = inputs.get("value", {})

            # Add spreadsheetId if not already present
            if "spreadsheetId" not in value:
                value["spreadsheetId"] = {
                    "__rl": False,
                    "value": f"={{{{ $(\'{spreadsheet_source_node}\').first().json.spreadsheetId }}}}"
                }
                inputs["value"] = value
                params["workflowInputs"] = inputs
                changes += 1

    return wf, changes


def add_user_lookup_nodes(wf, project_spreadsheet_id):
    """Replace Auth Check IF with User Lookup pattern in a main agent workflow.

    New flow:
    Webhook -> Lookup User (Google Sheets read from Users tab) -> Auth Gate (Code node) -> Read Learnings -> Enrich Prompt -> AI Agent

    The Auth Gate code node:
    - Checks if user was found (sheet returned a row)
    - Checks Active == TRUE
    - Checks ConversationsThisMonth < ConversationsLimit
    - Sets spreadsheetId into the output for downstream use
    """
    nodes = wf.get("nodes", [])
    connections = wf.get("connections", {})

    # Remove old Auth Check IF and Respond 401 nodes
    old_auth_check = None
    old_respond_401 = None
    for i, node in enumerate(nodes):
        if node["name"] == "Auth Check":
            old_auth_check = i
        if node["name"] == "Respond 401":
            old_respond_401 = i

    # Get Auth Check position for placement
    auth_pos = [300, 304]
    if old_auth_check is not None:
        auth_pos = nodes[old_auth_check].get("position", auth_pos)

    # Find the Google Sheets credential from Read Learnings node
    sheets_cred = None
    for node in nodes:
        if node["name"] == "Read Learnings":
            sheets_cred = node.get("credentials", {}).get("googleSheetsOAuth2Api")
            break

    if not sheets_cred:
        sheets_cred = {"id": "qpV1Z8tc0XDqAdRH", "name": "Google Sheets account"}

    # Remove old nodes (in reverse order to preserve indices)
    for idx in sorted([i for i in [old_auth_check, old_respond_401] if i is not None], reverse=True):
        del nodes[idx]

    # Remove old connections for Auth Check
    if "Auth Check" in connections:
        del connections["Auth Check"]

    # New node: Lookup User (Google Sheets read from Users tab in shared spreadsheet)
    lookup_user_node = {
        "parameters": {
            "operation": "read",
            "documentId": {"__rl": True, "value": SHARED_SPREADSHEET_ID, "mode": "id"},
            "sheetName": {"__rl": True, "value": "Users", "mode": "name"},
            "filtersUI": {
                "values": [
                    {
                        "lookupColumn": "AuthToken",
                        "lookupValue": "={{ $json.headers['x-auth-token'] }}"
                    }
                ]
            },
            "options": {}
        },
        "id": str(uuid.uuid4()).replace("-", "")[:32],
        "name": "Lookup User",
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.5,
        "position": [auth_pos[0], auth_pos[1]],
        "credentials": {"googleSheetsOAuth2Api": sheets_cred}
    }

    # New node: Auth Gate (Code node that validates user and extracts spreadsheetId)
    auth_gate_code = """const webhookData = $('Webhook').first().json;
const users = $input.all();

// No matching user found
if (!users || users.length === 0 || !users[0].json.AuthToken) {
  return [{ json: { authorized: false, error: 'Unauthorized' } }];
}

const user = users[0].json;

// Check if user is active
if (String(user.Active || '').toUpperCase() !== 'TRUE') {
  return [{ json: { authorized: false, error: 'Account inactive' } }];
}

// Check usage limit
const used = parseInt(user.ConversationsThisMonth || '0', 10);
const limit = parseInt(user.ConversationsLimit || '100', 10);
if (used >= limit) {
  return [{ json: { authorized: false, error: 'Monthly conversation limit reached (' + limit + '). Resets next month.' } }];
}

// User is authorized — pass through their config
return [{ json: {
  authorized: true,
  spreadsheetId: user.SpreadsheetId || '""" + project_spreadsheet_id + """',
  email: user.Email || '',
  plan: user.Plan || 'basic',
  conversationsUsed: used,
  conversationsLimit: limit,
  message: webhookData.body.message,
  sessionId: webhookData.body.sessionId || ''
}}];"""

    auth_gate_node = {
        "parameters": {"jsCode": auth_gate_code},
        "id": str(uuid.uuid4()).replace("-", "")[:32],
        "name": "Auth Gate",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [auth_pos[0] + 120, auth_pos[1]]
    }

    # New node: Check Auth (IF node that routes based on authorized flag)
    check_auth_node = {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                "conditions": [
                    {
                        "id": "auth-gate-check",
                        "leftValue": "={{ $json.authorized }}",
                        "rightValue": True,
                        "operator": {"type": "boolean", "operation": "true"}
                    }
                ],
                "combinator": "and"
            }
        },
        "id": str(uuid.uuid4()).replace("-", "")[:32],
        "name": "Check Auth",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [auth_pos[0] + 260, auth_pos[1]]
    }

    # New node: Respond Unauthorized (for failed auth)
    respond_unauth_node = {
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ JSON.stringify({ output: $json.error || 'Unauthorized', decisionTrace: '', toolsUsed: '' }) }}",
            "options": {"responseCode": "={{ $json.error && $json.error.includes('limit') ? 429 : 401 }}"}
        },
        "id": str(uuid.uuid4()).replace("-", "")[:32],
        "name": "Respond Unauthorized",
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "position": [auth_pos[0] + 380, auth_pos[1] + 200]
    }

    # Add new nodes
    nodes.extend([lookup_user_node, auth_gate_node, check_auth_node, respond_unauth_node])

    # Update Webhook connection to go to Lookup User
    connections["Webhook"] = {"main": [[{"node": "Lookup User", "type": "main", "index": 0}]]}

    # Lookup User -> Auth Gate
    connections["Lookup User"] = {"main": [[{"node": "Auth Gate", "type": "main", "index": 0}]]}

    # Auth Gate -> Check Auth
    connections["Auth Gate"] = {"main": [[{"node": "Check Auth", "type": "main", "index": 0}]]}

    # Check Auth true -> Read Learnings, false -> Respond Unauthorized
    connections["Check Auth"] = {
        "main": [
            [{"node": "Read Learnings", "type": "main", "index": 0}],
            [{"node": "Respond Unauthorized", "type": "main", "index": 0}]
        ]
    }

    # Update Enrich Prompt to also pass spreadsheetId
    for node in nodes:
        if node["name"] == "Enrich Prompt":
            js = node["parameters"]["jsCode"]
            # Add spreadsheetId extraction from Auth Gate
            if "spreadsheetId" not in js:
                # Prepend spreadsheetId extraction
                new_js = js.replace(
                    "const webhookData = $('Webhook').first().json;\nconst message = webhookData.body.message;",
                    "const authData = $('Auth Gate').first().json;\nconst message = authData.message || $('Webhook').first().json.body.message;\nconst spreadsheetId = authData.spreadsheetId || '';"
                )
                # Update return to include spreadsheetId
                new_js = new_js.replace(
                    "return [{ json: { message, learningsSection } }];",
                    "return [{ json: { message, learningsSection, spreadsheetId } }];"
                )
                node["parameters"]["jsCode"] = new_js
            break

    return wf


def main():
    dry_run = "--dry-run" in sys.argv

    print("Multi-Tenant Transformation")
    print(f"Dry run: {dry_run}")
    print()

    # Phase 1: Update tool sub-workflows
    all_tools = [
        (COSMETIC_TOOLS, COSMETIC_SPREADSHEET_ID, "Cosmetic"),
        (PROJECT_TOOLS, PROJECT_SPREADSHEET_ID, "Project"),
    ]

    for tools, ss_id, label in all_tools:
        print(f"=== {label} Tool Sub-Workflows ===")
        for filepath in tools:
            if not os.path.exists(filepath):
                print(f"  SKIP (not found): {filepath}")
                continue

            wf, changes = update_tool_workflow(filepath, ss_id)
            print(f"  {os.path.basename(filepath)}: {changes} spreadsheet IDs replaced")

            if not dry_run and changes > 0:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(wf, f, indent=2, ensure_ascii=False)
        print()

    # Phase 2: Update main agent workflows
    print("=== Main Agent Workflows ===")
    for filepath, ss_id in MAIN_WORKFLOWS.items():
        if not os.path.exists(filepath):
            print(f"  SKIP (not found): {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            wf = json.load(f)

        # Add user lookup nodes
        wf = add_user_lookup_nodes(wf, ss_id)

        # Add spreadsheetId to tool inputs
        wf, tool_changes = add_spreadsheet_to_tool_inputs(wf, "Enrich Prompt")

        print(f"  {os.path.basename(filepath)}:")
        print(f"    Added user lookup + auth gate nodes")
        print(f"    Added spreadsheetId to {tool_changes} tool nodes")

        if not dry_run:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(wf, f, indent=2, ensure_ascii=False)
    print()

    # Summary
    print("=" * 60)
    if dry_run:
        print("DRY RUN complete — no files modified")
    else:
        print("Multi-tenant transformation applied!")
    print()
    print("Post-transformation checklist:")
    print("  1. Add 'Users' tab to the shared AI Platform spreadsheet")
    print("     Columns: AuthToken, Email, Plan, SpreadsheetId, ProjectType,")
    print("              ConversationsThisMonth, ConversationsLimit, CreatedAt, Active")
    print("  2. Add at least one user row for testing")
    print("  3. Deploy all modified workflows to n8n")
    print("  4. Test end-to-end with a valid user token")
    print("=" * 60)


if __name__ == "__main__":
    main()
