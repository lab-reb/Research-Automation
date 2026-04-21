"""
research.py

Reads the Search Objective and Search Rules tabs from your Google Doc,
then uses Claude with web search to find contacts and writes them
directly to your Google Sheet — no copy-pasting needed.

Usage:
    python research.py

.env variables required:
    ANTHROPIC_API_KEY
    GOOGLE_DOC_ID       Google Doc containing Search Objective and Search Rules tabs
    GOOGLE_SHEET_ID     Google Sheet to write results into

How it works:
    1. Reads Search Objective and Search Rules from your Google Doc.
       Any edits you make to those tabs are picked up automatically on
       the next run — no changes to this script needed.
    2. Passes both tabs verbatim into a single Claude prompt with web
       search enabled. Claude searches official institutional pages
       (university directories, extension staff pages, etc.) to find
       contacts that match your criteria.
    3. Only includes contacts whose email was explicitly found on an
       official page. If an email can't be confirmed, the contact is
       skipped entirely.
    4. Appends results directly to the correct tab in your Google Sheet.
"""

import json
import os
import re
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_DOC_ID     = os.environ["GOOGLE_DOC_ID"]
GOOGLE_SHEET_ID   = os.environ["GOOGLE_SHEET_ID"]

TOKEN_PATH       = "token.json"
CREDENTIALS_PATH = "credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents.readonly",
]


# ── Google Auth ───────────────────────────────────────────────────────────────

def get_google_credentials() -> Credentials:
    creds = None
    if Path(TOKEN_PATH).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_PATH).exists():
                raise FileNotFoundError(
                    "credentials.json not found. Download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(TOKEN_PATH).write_text(creds.to_json())
    return creds


# ── Google Docs ───────────────────────────────────────────────────────────────

def read_doc_tab(doc: dict, tab_name: str) -> str:
    """Extract plain text from a named tab in a Google Doc."""
    for tab in doc.get("tabs", []):
        title = tab.get("tabProperties", {}).get("title", "")
        if title.lower() == tab_name.lower():
            body = tab.get("documentTab", {}).get("body", {})
            parts = []
            for element in body.get("content", []):
                for pe in element.get("paragraph", {}).get("elements", []):
                    text = pe.get("textRun", {}).get("content", "")
                    if text:
                        parts.append(text)
            return "".join(parts).strip()
    raise ValueError(f"Tab '{tab_name}' not found in Google Doc.")


def read_research_doc(creds: Credentials) -> dict:
    """
    Read the Search Objective and Search Rules tabs from the Google Doc.

    Both tabs are passed verbatim into the Claude prompt — so any edits
    you make in the doc (new criteria, different target tab name, updated
    contact rules) are picked up automatically without touching this script.
    """
    service = build("docs", "v1", credentials=creds)
    doc = service.documents().get(
        documentId=GOOGLE_DOC_ID, includeTabsContent=True
    ).execute()
    return {
        "objective": read_doc_tab(doc, "Search Objective"),
        "rules":     read_doc_tab(doc, "Search Rules"),
    }


# ── Google Sheets ─────────────────────────────────────────────────────────────

def extract_tab_name(objective_text: str) -> str:
    """
    Parse the target sheet tab name from the Search Objective text.
    Handles both inline ('Tab: Name') and next-line formats.
    Falls back to 'Research Results' if nothing is found.
    """
    lines = objective_text.splitlines()
    for i, line in enumerate(lines):
        match = re.search(
            r"(?:name of google sheets? tab|tab name|results?\s+tab|sheet tab)\s*[:\-]\s*(.*)",
            line,
            re.IGNORECASE,
        )
        if match:
            value = match.group(1).strip().strip('"').strip("'")
            if value:
                return value
            # Value is on the next non-empty line
            for next_line in lines[i + 1:]:
                next_line = next_line.strip().strip('"').strip("'")
                if next_line:
                    return next_line
    return "Research Results"


def ensure_tab_exists(creds: Credentials, tab_name: str) -> None:
    service = build("sheets", "v4", credentials=creds)
    spreadsheet = service.spreadsheets().get(spreadsheetId=GOOGLE_SHEET_ID).execute()
    existing = [s["properties"]["title"] for s in spreadsheet.get("sheets", [])]
    if tab_name not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=GOOGLE_SHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": tab_name}}}]},
        ).execute()
        print(f"  Created new tab: '{tab_name}'")


def write_headers_if_missing(creds: Credentials, tab_name: str, headers: list) -> None:
    service = build("sheets", "v4", credentials=creds)
    existing = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=GOOGLE_SHEET_ID, range=f"'{tab_name}'!A1:Z1")
        .execute()
    )
    if not existing.get("values"):
        service.spreadsheets().values().update(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=f"'{tab_name}'!A1",
            valueInputOption="RAW",
            body={"values": [headers]},
        ).execute()
        print(f"  Headers written: {headers}")


def append_rows(creds: Credentials, tab_name: str, rows: list) -> None:
    service = build("sheets", "v4", credentials=creds)
    service.spreadsheets().values().append(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{tab_name}'!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()


# ── Claude Research ───────────────────────────────────────────────────────────

def run_research_with_claude(objective: str, rules: str) -> list[dict]:
    """
    Pass the Search Objective and Search Rules directly to Claude with
    web search enabled. Claude searches official institutional pages to
    find contacts and returns them as structured JSON.

    Key rules baked into the prompt:
    - Only include contacts whose email was explicitly found on an
      official university or extension website.
    - If an email cannot be confirmed from an official source, skip
      that contact and find a different one.
    - Target official staff/faculty directory pages for efficiency
      (one page often yields multiple verified contacts).
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system_prompt = """You are a research assistant finding real contacts for outreach purposes.

You will be given a Search Objective and Search Rules. Read both carefully before
searching — they define exactly who to find, how many, and what fields to return.
The criteria may change between runs, so always follow the current instructions.

SEARCH STRATEGY:
- Target official university/extension staff directory pages directly.
  A single directory page often yields 5-10 verified contacts at once.
- Example searches: "NC State horticulture extension faculty directory",
  "University of Georgia CAES extension staff", "Purdue horticulture extension specialists"
- Prioritize department heads, program directors, extension specialists,
  and lead researchers over general staff.

EMAIL RULES (critical):
- Only include an email address that you found explicitly stated on an
  official .edu or institutional website.
- Do NOT guess, infer, or construct email addresses from name patterns.
- If you cannot find a confirmed email for a contact on an official page,
  skip that contact entirely and find a different one who has a listed email.

OUTPUT FORMAT:
Return a single JSON array and nothing else — no explanation, no markdown fences.
Each object must have exactly these keys:
  "name"         - Full name of the contact
  "email"        - Verified email from an official page
  "region"       - State and/or country
  "organization" - Name of the institution or department

Example:
[
  {
    "name": "Jane Smith",
    "email": "jsmith@university.edu",
    "region": "Georgia",
    "organization": "University of Georgia CAES Extension"
  }
]"""

    user_message = f"""Search Objective:
{objective}

Search Rules:
{rules}

Follow the Search Objective and Search Rules exactly. Search official university
and extension directory pages to find contacts. Only include contacts with a
verified email address from an official institutional page."""

    messages = [{"role": "user", "content": user_message}]

    print("  Sending objective and rules to Claude...")
    print(f"  Objective preview: {objective[:100].strip()}...")

    while True:
        for attempt in range(5):
            try:
                response = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=4096,
                    system=system_prompt,
                    tools=[{"type": "web_search_20250305", "name": "web_search"}],
                    messages=messages,
                )
                break
            except anthropic.RateLimitError:
                wait = 60 * (attempt + 1)
                print(f"  Rate limited — waiting {wait}s...")
                time.sleep(wait)
        else:
            raise RuntimeError("Exceeded rate limit retries.")

        if response.stop_reason == "end_turn":
            # Extract the final text response
            text = "\n".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
            break

        if response.stop_reason == "tool_use":
            # Claude is still searching — continue the agentic loop
            tool_count = sum(1 for b in response.content if b.type == "tool_use")
            print(f"  Claude ran {tool_count} search(es), continuing...")
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": getattr(block, "content", "Search completed."),
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            raise RuntimeError(f"Unexpected stop reason: {response.stop_reason}")

    # Parse the JSON response
    text = re.sub(r"```(?:json)?|```", "", text).strip()
    start = text.find("[")
    end   = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array found in Claude response:\n{text[:500]}")

    contacts = json.loads(text[start:end + 1])
    print(f"  Claude returned {len(contacts)} contacts.")
    return contacts


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("-- RESEARCH -------------------------------------------------")

    print("Authenticating with Google...")
    creds = get_google_credentials()

    # Step 1: Read the doc tabs — this is the source of truth for what
    # to search and how. Edit the doc, re-run, get different results.
    print("Reading Search Objective and Search Rules from Google Doc...")
    doc = read_research_doc(creds)
    print(f"  Objective: {doc['objective'][:120].strip()}...")
    print(f"  Rules length: {len(doc['rules'])} characters")

    # Step 2: Determine which sheet tab to write to (from the objective)
    tab_name = extract_tab_name(doc["objective"])
    print(f"  Target sheet tab: '{tab_name}'")

    # Step 3: Run Claude research — reads objective + rules, searches, returns contacts
    print("\nRunning Claude research with web search...")
    contacts = run_research_with_claude(doc["objective"], doc["rules"])

    if not contacts:
        print("No contacts returned. Check your Search Objective and Search Rules.")
        return

    # Step 4: Write directly to the sheet
    print(f"\nWriting {len(contacts)} contacts to '{tab_name}' tab...")
    ensure_tab_exists(creds, tab_name)
    write_headers_if_missing(
        creds, tab_name,
        ["Contact Name", "Email", "Region", "Organization", "Draft email", "Approved", "Sent"]
    )

    rows = [
        [
            c.get("name", ""),
            c.get("email", ""),
            c.get("region", ""),
            c.get("organization", ""),
            "",       # Draft email — filled by email script
            "FALSE",  # Approved
            "",       # Sent
        ]
        for c in contacts
        if c.get("name") and c.get("email")  # skip anything missing name or email
    ]

    append_rows(creds, tab_name, rows)

    print(f"\nDone. {len(rows)} contacts written to '{tab_name}'.")
    print("Review them in your sheet, then run the email script to draft outreach.")


if __name__ == "__main__":
    main()
