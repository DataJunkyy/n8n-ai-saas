# Cosmetic Formulation AI Assistant

An AI-powered cosmetic formulation assistant built on n8n. Chat with an AI agent to create, manage, and optimize cosmetic formulas — all stored in Google Sheets.

## What It Does

- **Create formulas** — describe a product (e.g., "moisturizer for dry skin") and the AI builds a complete formula
- **Manage ingredients** — add, edit, or remove ingredients with percentage tracking
- **Track versions** — every formula change is versioned with notes
- **Search ingredients** — find ingredients by name, function, or INCI name
- **Get summaries** — view formula details with full ingredient lists
- **Mobile-friendly Chat UI** — access from any phone via browser bookmark

## What's Included

| File | Description |
|------|-------------|
| `cosmetic-assistant-main.json` | Main AI agent workflow (Claude + 6 tools) |
| `tool-create-formula.json` | Creates a new formula in Google Sheets |
| `tool-list-formulas.json` | Lists all formulas with status |
| `tool-get-formula-details.json` | Gets full formula with ingredients |
| `tool-manage-ingredient.json` | Adds/edits/removes ingredients |
| `tool-update-formula.json` | Updates formula fields + versions changes |
| `tool-search-ingredients.json` | Searches ingredients by name/function |
| `cosmetic-chat-ui.json` | Mobile-friendly chat interface (HTML) |
| `SETUP.md` | Step-by-step setup checklist |

## Requirements

- **n8n** (Cloud or self-hosted, v1.0+)
- **Google Sheets** OAuth2 credential
- **Anthropic** API key (Claude)

## Spreadsheet Schema

Create a Google Sheet with 3 tabs:

**Formulas**
| FormulaID | Name | Category | Description | TargetPH | TotalPct | Status | CreatedAt | UpdatedAt | Notes |

**Ingredients**
| IngredientID | FormulaID | IngredientName | INCIName | Percentage | Phase | Function | MaxPct | SupplierNotes |

**FormulaVersions**
| VersionID | FormulaID | VersionNumber | ChangeDescription | ChangedBy | CreatedAt | Snapshot |

## Quick Start

1. Import all 8 JSON files into your n8n instance
2. Follow `SETUP.md` to connect credentials and create the spreadsheet
3. Activate all workflows
4. Open the Chat UI URL in your browser and start chatting

## Architecture

```
User (browser) → Chat UI (GET webhook, serves HTML)
                     ↓
              Main Agent (POST webhook)
              ├── Auth Check (X-Auth-Token)
              ├── AI Agent (Claude + tools)
              │   ├── tool-create-formula
              │   ├── tool-list-formulas
              │   ├── tool-get-formula-details
              │   ├── tool-manage-ingredient
              │   ├── tool-update-formula
              │   └── tool-search-ingredients
              └── Response (JSON with decision trace)
```

## License

MIT
