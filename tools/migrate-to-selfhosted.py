"""
Migrate n8n workflows from Cloud to a self-hosted instance.

Imports workflow JSON files into a new n8n instance, then remaps
tool sub-workflow IDs in the main agent workflows.

Usage:
    python tools/migrate-to-selfhosted.py <target_url> <target_api_key>

Reads workflow files from the local workflows/ directory.
Deploys tool sub-workflows first, then main workflows with remapped IDs.

Environment:
    SOURCE_API_KEY  — API key for source n8n Cloud (optional, for live export)
"""

import json
import os
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

# Workflow groups: tools first, then mains that reference them
COSMETIC_TOOLS = [
    ("workflows/tool-create-formula.json", "XzqRrVYprjCWlRVL"),
    ("workflows/tool-list-formulas.json", "5gISs6mMKm6kFGQS"),
    ("workflows/tool-get-formula-details.json", "q9okaghwRhbat149"),
    ("workflows/tool-manage-ingredient.json", "3zg7utWwqeSopdIt"),
    ("workflows/tool-update-formula.json", "XRlgUhzC4ARbHtvN"),
    ("workflows/tool-search-ingredients.json", "QEBeXFVt2RTMKI4U"),
]

PROJECT_TOOLS = [
    ("workflows/tool-list-tasks.json", "4xaQjKujons3MWh6"),
    ("workflows/tool-manage-task.json", "h29Xr3Uem0tbFuxT"),
    ("workflows/tool-create-document.json", "xTl4aCH8EQfUMnfF"),
    ("workflows/tool-get-project-summary.json", "21EaXJbz7s7JJMA3"),
]

SHARED_WORKFLOWS = [
    ("workflows/shared-log-interaction.json", "HvpDRQVudIit6DZX"),
    ("workflows/shared-log-feedback.json", "dMNZniMfBrav5sl7"),
    ("workflows/shared-learning-loop.json", "BEiOsCo3bwVSQnGI"),
    ("workflows/shared-monthly-reset.json", "znMFanljkEgsstdz"),
    ("workflows/user-registration.json", "oZZsFAeYA46yK9kZ"),
    ("workflows/stripe-webhook-handler.json", "he9rhHCvO2nWLyUZ"),
]

MAIN_WORKFLOWS = [
    ("workflows/cosmetic-assistant-main.json", "OWMMjqI1rSa4nPAG"),
    ("workflows/project-assistant-main.json", "PTln6pRFxXdzutSs"),
]

CHAT_UIS = [
    ("workflows/cosmetic-chat-ui.json", "XyqD0caTgjgpQa4P"),
    ("workflows/project-assistant-chat-ui.json", "LOvS3BK4D12oitzb"),
]


def n8n_api(base_url, api_key, method, path, data=None):
    """Make an n8n API call."""
    url = f"{base_url}/api/v1{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("X-N8N-API-KEY", api_key)
    if body:
        req.add_header("Content-Type", "application/json")
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read().decode())


def import_workflow(base_url, api_key, filepath):
    """Import a workflow JSON file into the target instance. Returns new workflow ID."""
    with open(filepath, "r", encoding="utf-8") as f:
        wf = json.load(f)

    payload = {
        "name": wf["name"],
        "nodes": wf["nodes"],
        "connections": wf["connections"],
        "settings": wf.get("settings", {}),
    }

    result = n8n_api(base_url, api_key, "POST", "/workflows", payload)
    return result["id"], result["name"]


def remap_workflow_ids(filepath, id_map):
    """Replace old workflow IDs with new ones in a workflow file. Returns modified workflow dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    replacements = 0
    for old_id, new_id in id_map.items():
        if old_id in content:
            content = content.replace(old_id, new_id)
            replacements += 1

    return json.loads(content), replacements


def activate_workflow(base_url, api_key, wf_id):
    """Try to activate a workflow. Returns True if successful."""
    try:
        n8n_api(base_url, api_key, "POST", f"/workflows/{wf_id}/activate")
        return True
    except Exception:
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/migrate-to-selfhosted.py <target_url> <target_api_key>")
        print()
        print("  target_url     — e.g., https://n8n.yourdomain.com")
        print("  target_api_key — API key for the target instance")
        print()
        print("Options:")
        print("  --dry-run      — show what would be done without making changes")
        sys.exit(1)

    target_url = sys.argv[1].rstrip("/")
    target_key = sys.argv[2]
    dry_run = "--dry-run" in sys.argv

    print(f"Target: {target_url}")
    print(f"Dry run: {dry_run}")
    print()

    # Verify target is reachable
    if not dry_run:
        try:
            n8n_api(target_url, target_key, "GET", "/workflows?limit=1")
            print("Target instance connected successfully.")
        except Exception as e:
            print(f"ERROR: Cannot connect to target: {e}")
            sys.exit(1)
    print()

    # Phase 1: Import tool sub-workflows (order matters — these get new IDs)
    id_map = {}  # old_id -> new_id
    all_groups = [
        ("Cosmetic Tools", COSMETIC_TOOLS),
        ("Project Tools", PROJECT_TOOLS),
        ("Shared Workflows", SHARED_WORKFLOWS),
    ]

    for group_name, workflows in all_groups:
        print(f"=== {group_name} ===")
        for filepath, old_id in workflows:
            if not os.path.exists(filepath):
                print(f"  SKIP (file not found): {filepath}")
                continue

            if dry_run:
                print(f"  Would import: {filepath} (old ID: {old_id})")
                id_map[old_id] = f"NEW_{old_id}"
            else:
                new_id, name = import_workflow(target_url, target_key, filepath)
                id_map[old_id] = new_id
                print(f"  Imported: {name}")
                print(f"    {old_id} -> {new_id}")

                activated = activate_workflow(target_url, target_key, new_id)
                if activated:
                    print(f"    Activated")
                else:
                    print(f"    Skipped activation (sub-workflow)")
        print()

    # Phase 2: Import main workflows with remapped IDs
    print("=== Main Agent Workflows ===")
    for filepath, old_id in MAIN_WORKFLOWS:
        if not os.path.exists(filepath):
            print(f"  SKIP (file not found): {filepath}")
            continue

        if dry_run:
            wf, count = remap_workflow_ids(filepath, id_map)
            print(f"  Would import: {filepath} ({count} IDs to remap)")
        else:
            wf, count = remap_workflow_ids(filepath, id_map)
            print(f"  Remapped {count} workflow IDs in {filepath}")

            payload = {
                "name": wf["name"],
                "nodes": wf["nodes"],
                "connections": wf["connections"],
                "settings": wf.get("settings", {}),
            }
            result = n8n_api(target_url, target_key, "POST", "/workflows", payload)
            new_id = result["id"]
            id_map[old_id] = new_id
            print(f"  Imported: {wf['name']}")
            print(f"    {old_id} -> {new_id}")

            activated = activate_workflow(target_url, target_key, new_id)
            print(f"    {'Activated' if activated else 'Activation failed'}")
    print()

    # Phase 3: Import Chat UIs (need webhook URL remapping for new domain)
    print("=== Chat UIs ===")
    for filepath, old_id in CHAT_UIS:
        if not os.path.exists(filepath):
            print(f"  SKIP (file not found): {filepath}")
            continue

        if dry_run:
            print(f"  Would import: {filepath}")
            print(f"    NOTE: Update instance URL in Chat UI HTML after import")
        else:
            # Remap the n8n instance URL in Chat UI code
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace Cloud URL with target URL
            cloud_host = "princeadarkwah.app.n8n.cloud"
            target_host = target_url.replace("https://", "").replace("http://", "")
            if cloud_host in content:
                content = content.replace(cloud_host, target_host)
                print(f"  Remapped instance URL: {cloud_host} -> {target_host}")

            wf = json.loads(content)
            payload = {
                "name": wf["name"],
                "nodes": wf["nodes"],
                "connections": wf["connections"],
                "settings": wf.get("settings", {}),
            }
            result = n8n_api(target_url, target_key, "POST", "/workflows", payload)
            new_id = result["id"]
            id_map[old_id] = new_id
            print(f"  Imported: {wf['name']}")
            print(f"    {old_id} -> {new_id}")

            activated = activate_workflow(target_url, target_key, new_id)
            print(f"    {'Activated' if activated else 'Activation failed'}")
    print()

    # Summary
    print("=" * 60)
    print(f"Migration complete: {len(id_map)} workflows")
    print()
    print("ID Mapping (old -> new):")
    for old_id, new_id in id_map.items():
        print(f"  {old_id} -> {new_id}")
    print()
    print("Post-migration checklist:")
    print("  1. Create credentials on the new instance (Google Sheets, Anthropic, Google Docs)")
    print("  2. Update credential IDs in each workflow")
    print("  3. Update spreadsheet IDs if using new sheets")
    print("  4. Set WEBHOOK_URL environment variable to your domain")
    print("  5. Update auth tokens if desired")
    print("  6. Test each workflow end-to-end")
    print("=" * 60)

    # Save mapping to file
    mapping_file = "tools/migration-id-map.json"
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(id_map, f, indent=2)
    print(f"\nID mapping saved to: {mapping_file}")


if __name__ == "__main__":
    main()
