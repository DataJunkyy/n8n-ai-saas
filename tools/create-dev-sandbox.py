"""
Create a dev sandbox for an n8n project.

Reads production workflow JSON files and creates dev versions with:
- Workflow name suffixed with [DEV]
- Webhook paths suffixed with -dev
- New unique webhookIds
- Optionally a different spreadsheet ID

Deploys the dev workflows to n8n Cloud via API.

Usage:
    python tools/create-dev-sandbox.py <config_file>

Config file is JSON:
{
    "project_name": "Cosmetic Formulator",
    "n8n_base_url": "https://princeadarkwah.app.n8n.cloud",
    "dev_spreadsheet_id": "NEW_SPREADSHEET_ID",  // optional, leave null to keep same
    "prod_spreadsheet_id": "1cLv6rS_...",
    "workflows": [
        {"file": "workflows/cosmetic-assistant-main.json", "is_main": true},
        {"file": "workflows/tool-create-formula.json"},
        ...
    ]
}
"""

import json
import os
import re
import sys
import uuid
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

# n8n API key from environment or hardcoded for now
API_KEY = os.environ.get("N8N_API_KEY", "")
BASE_URL = "https://princeadarkwah.app.n8n.cloud"


def n8n_api(method, path, data=None):
    """Make an n8n API call."""
    url = f"{BASE_URL}/api/v1{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("X-N8N-API-KEY", API_KEY)
    if body:
        req.add_header("Content-Type", "application/json")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())


def make_dev_version(workflow: dict, dev_spreadsheet_id: str | None, prod_spreadsheet_id: str | None) -> dict:
    """Transform a production workflow into a dev version."""
    wf = json.loads(json.dumps(workflow))  # deep copy

    # Suffix name with [DEV]
    if "name" in wf:
        wf["name"] = wf["name"] + " [DEV]"

    # Process nodes
    for node in wf.get("nodes", []):
        params = node.get("parameters", {})

        # Replace webhook paths with -dev suffix
        if node.get("type") == "n8n-nodes-base.webhook":
            if "path" in params:
                params["path"] = params["path"] + "-dev"
            # Generate new webhookId
            node["webhookId"] = str(uuid.uuid4())

        # Replace spreadsheet IDs if dev spreadsheet provided
        if dev_spreadsheet_id and prod_spreadsheet_id:
            node_str = json.dumps(node)
            if prod_spreadsheet_id in node_str:
                node_str = node_str.replace(prod_spreadsheet_id, dev_spreadsheet_id)
                updated = json.loads(node_str)
                node.clear()
                node.update(updated)

        # Update webhook URLs in Code node jsCode (for Chat UIs)
        if node.get("type") == "n8n-nodes-base.code" and "jsCode" in params:
            js = params["jsCode"]
            # Add -dev to webhook paths in URL strings
            js = re.sub(
                r"(/webhook/[a-zA-Z0-9-]+)(?=['\"])",
                r"\1-dev",
                js,
            )
            params["jsCode"] = js

        # Update webhook URLs in executeWorkflow references
        # (tool sub-workflows don't need path changes — they're called by ID)

    return wf


def deploy_workflow(workflow: dict) -> dict:
    """Deploy a workflow to n8n Cloud. Returns the created workflow."""
    payload = {
        "name": workflow["name"],
        "nodes": workflow["nodes"],
        "connections": workflow["connections"],
        "settings": workflow.get("settings", {}),
    }

    result = n8n_api("POST", "/workflows", payload)
    workflow_id = result["id"]
    print(f"  Created: {workflow['name']} (ID: {workflow_id})")

    # Try to activate (may fail for sub-workflows without webhook triggers)
    try:
        n8n_api("POST", f"/workflows/{workflow_id}/activate")
        print(f"  Activated: {workflow_id}")
    except Exception as e:
        print(f"  Skipped activation (sub-workflow): {e}")

    return result


def main():
    if not API_KEY:
        print("Error: Set N8N_API_KEY environment variable")
        print("  export N8N_API_KEY=your-api-key")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python create-dev-sandbox.py <config.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        config = json.load(f)

    project = config["project_name"]
    dev_ss = config.get("dev_spreadsheet_id")
    prod_ss = config.get("prod_spreadsheet_id")

    print(f"Creating dev sandbox for: {project}")
    print(f"Dev spreadsheet: {dev_ss or 'same as prod'}")
    print()

    deployed = []

    for wf_config in config["workflows"]:
        filepath = wf_config["file"]
        print(f"Processing: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        dev_wf = make_dev_version(workflow, dev_ss, prod_ss)

        # Save locally
        dev_filename = os.path.basename(filepath).replace(".json", "-dev.json")
        dev_path = os.path.join("workflows", dev_filename)
        with open(dev_path, "w", encoding="utf-8") as f:
            json.dump(dev_wf, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {dev_path}")

        # Deploy to n8n
        result = deploy_workflow(dev_wf)
        deployed.append({
            "name": dev_wf["name"],
            "id": result["id"],
            "file": dev_path,
        })
        print()

    # Summary
    print("=" * 60)
    print(f"Dev sandbox created: {len(deployed)} workflows deployed")
    print()
    for d in deployed:
        print(f"  {d['name']}: {d['id']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
