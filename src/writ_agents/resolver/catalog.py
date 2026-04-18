"""Embedded connector catalog (~20 entries)."""

from __future__ import annotations

from pydantic import BaseModel


class ConnectorEntry(BaseModel):
    id: str
    name: str
    source: str  # "mcp" | "oauth" | "manual"
    icon: str
    aliases: list[str]
    description: str
    mcp_url: str | None = None


CATALOG: list[ConnectorEntry] = [
    ConnectorEntry(
        id="gmail",
        name="Gmail",
        source="mcp",
        icon="📧",
        aliases=["email", "gmail", "google email", "inbox", "emails", "mail"],
        description="Read and send emails via Gmail",
    ),
    ConnectorEntry(
        id="outlook",
        name="Outlook",
        source="mcp",
        icon="📨",
        aliases=["outlook", "microsoft email", "office 365 email", "exchange"],
        description="Read and send emails via Microsoft Outlook",
    ),
    ConnectorEntry(
        id="imap",
        name="Generic Email (IMAP)",
        source="oauth",
        icon="📬",
        aliases=["imap", "generic email", "custom email", "company email"],
        description="Read emails from any IMAP-compatible mail server",
    ),
    ConnectorEntry(
        id="slack",
        name="Slack",
        source="mcp",
        icon="💬",
        aliases=[
            "slack",
            "slack messages",
            "slack channel",
            "team chat",
            "instant messages",
        ],
        description="Send and read Slack messages",
    ),
    ConnectorEntry(
        id="teams",
        name="Microsoft Teams",
        source="mcp",
        icon="🟦",
        aliases=[
            "teams",
            "microsoft teams",
            "ms teams",
            "teams chat",
            "teams messages",
        ],
        description="Send and read Microsoft Teams messages",
    ),
    ConnectorEntry(
        id="hubspot",
        name="HubSpot",
        source="mcp",
        icon="🔶",
        aliases=["hubspot", "crm", "customer records", "contacts", "deals", "pipeline"],
        description="Read and update HubSpot CRM records",
    ),
    ConnectorEntry(
        id="salesforce",
        name="Salesforce",
        source="mcp",
        icon="☁️",
        aliases=[
            "salesforce",
            "sfdc",
            "salesforce crm",
            "leads",
            "opportunities",
            "accounts",
        ],
        description="Access Salesforce CRM data and records",
    ),
    ConnectorEntry(
        id="pipedrive",
        name="Pipedrive",
        source="mcp",
        icon="🎯",
        aliases=["pipedrive", "pipedrive crm", "sales pipeline", "deals pipeline"],
        description="Read and update Pipedrive deals and contacts",
    ),
    ConnectorEntry(
        id="google_sheets",
        name="Google Sheets",
        source="mcp",
        icon="📊",
        aliases=[
            "google sheets",
            "spreadsheet",
            "sheets",
            "excel online",
            "google spreadsheet",
        ],
        description="Read and write Google Sheets data",
    ),
    ConnectorEntry(
        id="airtable",
        name="Airtable",
        source="mcp",
        icon="🗃️",
        aliases=["airtable", "airtable base", "airtable table", "no-code database"],
        description="Read and write Airtable records",
    ),
    ConnectorEntry(
        id="notion",
        name="Notion",
        source="mcp",
        icon="📝",
        aliases=["notion", "notion docs", "notion database", "notion pages", "wiki"],
        description="Read and write Notion pages and databases",
    ),
    ConnectorEntry(
        id="postgresql",
        name="PostgreSQL",
        source="mcp",
        icon="🐘",
        aliases=[
            "database",
            "postgres",
            "postgresql",
            "sql database",
            "db",
            "relational database",
        ],
        description="Query PostgreSQL databases",
    ),
    ConnectorEntry(
        id="google_drive",
        name="Google Drive",
        source="mcp",
        icon="📁",
        aliases=["google drive", "drive", "gdrive", "google files", "file storage"],
        description="Read files from Google Drive",
    ),
    ConnectorEntry(
        id="dropbox",
        name="Dropbox",
        source="mcp",
        icon="📦",
        aliases=["dropbox", "dropbox files", "file sharing"],
        description="Access files stored in Dropbox",
    ),
    ConnectorEntry(
        id="zendesk",
        name="Zendesk",
        source="mcp",
        icon="🎫",
        aliases=[
            "zendesk",
            "support tickets",
            "help desk",
            "customer support tickets",
            "tickets",
        ],
        description="Read and update Zendesk support tickets",
    ),
    ConnectorEntry(
        id="jira",
        name="Jira",
        source="mcp",
        icon="🔷",
        aliases=[
            "jira",
            "jira tickets",
            "project management",
            "issues",
            "bug tracker",
            "task tracker",
        ],
        description="Read and create Jira issues",
    ),
    ConnectorEntry(
        id="google_calendar",
        name="Google Calendar",
        source="mcp",
        icon="📅",
        aliases=[
            "google calendar",
            "calendar",
            "schedule",
            "meetings",
            "appointments",
            "events",
        ],
        description="Read and create Google Calendar events",
    ),
    ConnectorEntry(
        id="web_search",
        name="Web Search",
        source="mcp",
        icon="🔍",
        aliases=[
            "web search",
            "search",
            "internet search",
            "google search",
            "look up online",
            "search the web",
        ],
        description="Search the web for current information",
    ),
    ConnectorEntry(
        id="manual",
        name="Manual / Custom",
        source="manual",
        icon="🔧",
        aliases=["manual", "custom", "other", "api", "webhook", "custom integration"],
        description="Custom integration requiring manual setup",
    ),
]


def get_catalog() -> list[ConnectorEntry]:
    """Return the full embedded connector catalog."""
    return CATALOG


def find_by_id(connector_id: str) -> ConnectorEntry | None:
    """Look up a connector by its ID."""
    return next((c for c in CATALOG if c.id == connector_id), None)
