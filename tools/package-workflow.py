"""
Package n8n workflows for marketplace distribution.

Reads workflow JSON files, strips sensitive data (credential IDs, spreadsheet IDs,
auth tokens, instance URLs), and outputs clean files ready for sharing/selling.

Usage:
    python tools/package-workflow.py <project_name> <output_dir> <workflow_files...>

Example:
    python tools/package-workflow.py cosmetic-formulator packages/cosmetic-formulator \
        workflows/cosmetic-assistant-main.json \
        workflows/tool-create-formula.json \
        workflows/cosmetic-chat-ui.json
"""

import json
import os
import re
import sys

# Patterns to replace (value -> placeholder)
# Add project-specific entries before calling package()
SENSITIVE_PATTERNS = {
    # Credential IDs (real n8n alphanumeric IDs)
    "qpV1Z8tc0XDqAdRH": "YOUR_GOOGLE_SHEETS_CREDENTIAL_ID",
    "WsdnsArOUZJ9ssTS": "YOUR_ANTHROPIC_CREDENTIAL_ID",
    "lEnWoDkNdZXZ3iv2": "YOUR_GOOGLE_DOCS_CREDENTIAL_ID",
    # Auth token
    "b9cd461c9cd9a90ee16c3dd40f8637e3": "YOUR_AUTH_TOKEN",
    # n8n instance URL
    "princeadarkwah.app.n8n.cloud": "YOUR_N8N_INSTANCE.app.n8n.cloud",
}

# Spreadsheet IDs (project-specific)
SPREADSHEET_IDS = {
    "1cLv6rS_YjlTGVGrrpWFt7TMz4el1SOsYwlDmzwOwKXI": "YOUR_PROJECT_SPREADSHEET_ID",
    "1FLuoMIZiP-fF_p--9uNhp5b6bRaBIS3QmLHuOU0SSHY": "YOUR_PROJECT_SPREADSHEET_ID",
    "1IDVVby9y7ccYwi5NRjXCx5HRjao2NJ3KNUKDrv-Y3bI": "YOUR_SHARED_SPREADSHEET_ID",
}


def strip_sensitive(text: str) -> tuple[str, list[str]]:
    """Replace all sensitive values in text. Returns (clean_text, list_of_replacements)."""
    replacements = []
    all_patterns = {**SENSITIVE_PATTERNS, **SPREADSHEET_IDS}

    for real_value, placeholder in all_patterns.items():
        if real_value in text:
            count = text.count(real_value)
            text = text.replace(real_value, placeholder)
            replacements.append(f"  Replaced {count}x: {placeholder}")

    return text, replacements


def generate_setup_checklist(workflows: list[dict], project_name: str) -> str:
    """Analyze workflows and generate a setup checklist."""
    cred_types = set()
    has_webhook = False
    has_sheets = False
    has_anthropic = False
    has_auth_token = False
    webhook_paths = []

    for wf in workflows:
        text = json.dumps(wf)
        if "YOUR_AUTH_TOKEN" in text:
            has_auth_token = True
        for node in wf.get("nodes", []):
            creds = node.get("credentials", {})
            for cred_type in creds:
                cred_types.add(cred_type)
                if cred_type == "googleSheetsOAuth2Api":
                    has_sheets = True
                if cred_type == "anthropicApi":
                    has_anthropic = True
            if node.get("type") == "n8n-nodes-base.webhook":
                has_webhook = True
                path = node.get("parameters", {}).get("path", "")
                if path:
                    webhook_paths.append(path)

    lines = [
        f"# {project_name} — Setup Checklist",
        "",
        "Complete these steps after importing the workflow JSON files into your n8n instance.",
        "",
        "## 1. Create Required Credentials",
        "",
    ]

    if has_sheets:
        lines.append("- [ ] **Google Sheets OAuth2** — Connect your Google account")
        lines.append("  - Go to n8n Settings → Credentials → Add Credential → Google Sheets")
        lines.append("  - After connecting, note the credential ID from the URL")
        lines.append("")
    if has_anthropic:
        lines.append("- [ ] **Anthropic API** — Add your Anthropic API key")
        lines.append("  - Go to n8n Settings → Credentials → Add Credential → Anthropic")
        lines.append("  - Paste your API key from console.anthropic.com")
        lines.append("")
    if "googleDocsOAuth2Api" in cred_types:
        lines.append("- [ ] **Google Docs OAuth2** — Connect your Google account")
        lines.append("")

    lines.extend([
        "## 2. Update Credential IDs in Workflows",
        "",
        "After creating credentials, update the placeholder IDs in each workflow:",
        "",
        "1. Open each workflow in the n8n editor",
        "2. Click on nodes with a warning icon (missing credentials)",
        "3. Select your credential from the dropdown",
        "4. Save the workflow",
        "",
    ])

    lines.extend([
        "## 3. Create Your Spreadsheet",
        "",
        "Option A: Import the included `setup-spreadsheet.json` workflow and run it once.",
        "",
        "Option B: Manually create a Google Sheet with the required tabs and headers",
        "(see README for schema details).",
        "",
        "After creating the spreadsheet, update `YOUR_PROJECT_SPREADSHEET_ID` in all workflows.",
        "",
    ])

    if has_auth_token:
        lines.extend([
            "## 4. Set Auth Token",
            "",
            "Generate a random token for webhook authentication:",
            "```bash",
            "openssl rand -hex 16",
            "```",
            "",
            "Replace `YOUR_AUTH_TOKEN` in all workflow Code/IF nodes and Chat UI HTML.",
            "",
        ])

    lines.extend([
        f"## {'5' if has_auth_token else '4'}. Activate and Test",
        "",
        "1. Activate all workflows (toggle ON in the workflow list)",
        "2. Test with curl:",
        "```bash",
        f"curl -X POST https://YOUR_N8N_INSTANCE.app.n8n.cloud/webhook/{webhook_paths[0] if webhook_paths else 'your-webhook-path'} \\",
        "  -H 'Content-Type: application/json' \\",
        "  -H 'X-Auth-Token: YOUR_AUTH_TOKEN' \\",
        "  -d '{\"message\": \"hello\"}'",
        "```",
        "",
    ])

    return "\n".join(lines)


def package_workflows(project_name: str, output_dir: str, input_files: list[str]):
    """Package workflow files for distribution."""
    os.makedirs(output_dir, exist_ok=True)

    print(f"Packaging project: {project_name}")
    print(f"Output directory: {output_dir}")
    print(f"Input files: {len(input_files)}")
    print()

    all_workflows = []

    for filepath in input_files:
        filename = os.path.basename(filepath)
        print(f"Processing: {filename}")

        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()

        clean, replacements = strip_sensitive(raw)

        if replacements:
            for r in replacements:
                print(r)
        else:
            print("  No sensitive data found")

        # Parse to validate JSON
        workflow = json.loads(clean)
        all_workflows.append(workflow)

        # Write clean file
        out_path = os.path.join(output_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

        print(f"  -> {out_path}")
        print()

    # Generate setup checklist
    checklist = generate_setup_checklist(all_workflows, project_name)
    checklist_path = os.path.join(output_dir, "SETUP.md")
    with open(checklist_path, "w", encoding="utf-8") as f:
        f.write(checklist)
    print(f"Generated: {checklist_path}")

    # Summary
    print()
    print("=" * 60)
    print(f"Package complete: {len(input_files)} workflows -> {output_dir}")
    print("Next steps:")
    print("  1. Review the clean JSON files for any remaining secrets")
    print("  2. Add a README.md with project description")
    print("  3. Test by importing into a fresh n8n instance")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python package-workflow.py <project_name> <output_dir> <file1.json> [file2.json ...]")
        sys.exit(1)

    project_name = sys.argv[1]
    output_dir = sys.argv[2]
    input_files = sys.argv[3:]

    package_workflows(project_name, output_dir, input_files)
