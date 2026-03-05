# AI Project Management Assistant

An AI-powered project management assistant built on n8n. Chat with an AI agent to create tasks, track progress, generate documents, and get project summaries — all stored in Google Sheets.

## What It Does

- **Manage tasks** — create, update, and organize tasks with priority levels, due dates, and status tracking
- **Track progress** — list all tasks filtered by status, priority, or project
- **Create documents** — generate project documents (briefs, reports, plans) in Google Docs
- **Get summaries** — view project-level summaries with task breakdowns and completion stats
- **Mobile-friendly Chat UI** — access from any phone via browser bookmark

## What's Included

| File | Description |
|------|-------------|
| `project-assistant-main.json` | Main AI agent workflow (Claude + 4 tools) |
| `tool-list-tasks.json` | Lists tasks with filtering |
| `tool-manage-task.json` | Creates/updates/deletes tasks |
| `tool-create-document.json` | Generates Google Docs from AI |
| `tool-get-project-summary.json` | Project overview with stats |
| `project-assistant-chat-ui.json` | Mobile-friendly chat interface (HTML) |
| `SETUP.md` | Step-by-step setup checklist |

## Requirements

- **n8n** (Cloud or self-hosted, v1.0+)
- **Google Sheets** OAuth2 credential
- **Google Docs** OAuth2 credential
- **Anthropic** API key (Claude)

## Spreadsheet Schema

Create a Google Sheet with 2 tabs:

**Tasks**
| TaskID | ProjectName | TaskName | Description | Status | Priority | DueDate | AssignedTo | CreatedAt | UpdatedAt | Notes |

**Projects**
| ProjectID | ProjectName | Description | Status | CreatedAt |

## Quick Start

1. Import all 7 JSON files into your n8n instance
2. Follow `SETUP.md` to connect credentials and create the spreadsheet
3. Activate all workflows
4. Open the Chat UI URL in your browser and start chatting

## Architecture

```
User (browser) -> Chat UI (GET webhook, serves HTML)
                     |
              Main Agent (POST webhook)
              +-- Auth Check (X-Auth-Token)
              +-- AI Agent (Claude + tools)
              |   +-- tool-list-tasks
              |   +-- tool-manage-task
              |   +-- tool-create-document
              |   +-- tool-get-project-summary
              +-- Response (JSON with decision trace)
```

## License

MIT
