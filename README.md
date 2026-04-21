# Research Automation Setup Guide

This tool reads your search criteria from a Google Doc, uses AI with live web search to find real contacts (with verified emails), and writes them directly to your Google Sheet — ready for the email automation script to pick up.

---

## What You'll Need

- A Windows computer
- A Google account
- An Anthropic account (for the AI)
- The shared Google Sheet and Google Doc links from Rachel

---

## Step 1 — Install the Required Programs

Install these three programs in order. Use all the default settings during installation.

1. **Python** — https://www.python.org/downloads/
   - On the first screen, check the box that says **"Add Python to PATH"** before clicking Install

2. **Git** — https://git-scm.com/download/win

3. **Cursor** — https://www.cursor.com

---

## Step 2 — Install Claude in Cursor

1. Open **Cursor**
2. Click the **Extensions** icon in the left sidebar (it looks like four squares)
3. In the search bar, type `Claude Code`
4. Click the result published by **Anthropic** and click **Install**
5. Once installed, click the **Claude** icon that appears in the left sidebar
6. Sign in with your Anthropic account (the same one you'll use for your API key in Step 5)

Claude will now be available inside Cursor to help you if anything goes wrong or you have questions about the script.

---

## Step 3 — Download This Project

1. Open **Cursor**
2. Open the Terminal inside Cursor: go to the top menu → **Terminal** → **New Terminal**
3. Paste this command and press Enter:

```
git clone https://github.com/lab-reb/Research-Automation.git
```

4. Then navigate into the project folder:

```
cd Research-Automation
```

---

## Step 4 — Install Python Dependencies

In the same terminal, paste this and press Enter:

```
pip install anthropic google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dotenv
```

Wait for it to finish (it may take a minute).

---

## Step 5 — Get Your Anthropic API Key

1. Go to https://console.anthropic.com and sign in
2. Click **API Keys** in the left menu
3. Click **Create Key**, name it anything (e.g. "Research Automation")
4. Copy the key — it starts with `sk-ant-...`
5. Keep this tab open, you'll need it shortly

---

## Step 6 — Set Up Google Cloud (for Sheets & Docs access)

This gives the script permission to read your Google Doc and write to your Google Sheet.

1. Go to https://console.cloud.google.com and sign in with your Google account
2. Click **Select a project** at the top → **New Project**
3. Name it `Research Automation` and click **Create**
4. In the search bar at the top, search for and enable these two APIs one at a time:
   - **Google Sheets API** → click Enable
   - **Google Docs API** → click Enable
5. Go to **APIs & Services** → **Credentials** in the left menu
6. Click **Create Credentials** → **OAuth client ID**
7. If prompted to configure a consent screen, click **Configure Consent Screen**:
   - Choose **External** → click Create
   - Fill in "App name" (anything, e.g. "Research Tool") and your email → Save and Continue through all steps
8. Back on Create Credentials → OAuth client ID:
   - Application type: **Desktop app**
   - Name it anything → click **Create**
9. Click **Download JSON** on the popup
10. Rename the downloaded file to `credentials.json`
11. Move `credentials.json` into the `Research-Automation` folder on your computer

---

## Step 7 — Create Your .env File

In the Cursor terminal, paste this command (replace each value with your own):

```
python -c "
with open('.env', 'w') as f:
    f.write('ANTHROPIC_API_KEY=paste-your-anthropic-key-here\n')
    f.write('GOOGLE_SHEET_ID=paste-your-sheet-id-here\n')
    f.write('GOOGLE_DOC_ID=paste-your-doc-id-here\n')
"
```

**Where to find your Sheet ID and Doc ID:**

Open the shared links Rachel sent you and look at the URL in your browser:

- Google Sheet URL: `https://docs.google.com/spreadsheets/d/`**THIS-IS-YOUR-ID**`/edit`
- Google Doc URL: `https://docs.google.com/document/d/`**THIS-IS-YOUR-ID**`/edit`

Copy the long string of letters and numbers between `/d/` and `/edit` — that's your ID.

---

## Step 8 — Run the Script

In the Cursor terminal, run:

```
python research.py
```

The first time you run it, a browser window will open asking you to sign in to Google and grant permission. Click through and approve — this only happens once.

---

## How It Works

Each time you run `python research.py`:

1. It reads your **Search Objective** and **Search Rules** from the shared Google Doc
2. It uses AI with live web search to find contacts that match your criteria — only including people whose email was found on an official institutional page (university directory, extension staff page, etc.)
3. It creates a new tab in your Google Sheet (named in your Search Objective) if it doesn't exist yet
4. It writes the contacts directly to that tab with columns: **Contact Name**, **Email**, **Region**, **Organization**

From there, the email automation script can pick up those contacts and draft outreach emails.

---

## Editing the Search Objective and Search Rules

The script reads two tabs from the shared Google Doc to decide who to search for. You can edit these at any time — changes take effect the next time you run the script.

Open the Google Doc Rachel shared with you and click the tabs at the top of the document.

---

### Search Objective tab

This tells the script who to find and where to put the results. Edit this to change things like:

- **Who to target** — e.g. "Find 20 university extension specialists in horticulture"
- **Which regions** — e.g. "Focus on the Southeast US"
- **Target sheet tab** — include a line like `Sheet tab: Southeast Horticulture` to control where results are written in your Google Sheet

---

### Search Rules tab

This sets the boundaries for what counts as a valid contact. Edit this to change things like:

- **Institution type** — e.g. "Only include contacts at land-grant universities"
- **Role requirements** — e.g. "Must be an extension specialist or department head"
- **Email rules** — e.g. "Only include contacts with a .edu email address"
- **Things to exclude** — e.g. "Do not include graduate students"

---

**Tips:**
- Be specific — the more detail you give, the more targeted the results will be
- If the results don't look right, update the Search Objective or Search Rules and run the script again — new contacts will be added to the sheet
- The script never overwrites existing rows, it only adds new ones

---

## Getting Updates

If Rachel sends you a message saying the script has been updated, here's how to download the latest version:

1. Open **Cursor**
2. Open the Terminal: **Terminal** → **New Terminal**
3. Navigate to the project folder:

```
cd Research-Automation
```

4. Run this command to download the latest version:

```
git pull
```

That's it — your script is now up to date.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python: command not found` | Reinstall Python and make sure to check "Add Python to PATH" |
| `ModuleNotFoundError` | Re-run the `pip install ...` command from Step 4 |
| `credentials.json not found` | Make sure the file is in the `Research-Automation` folder |
| Google sign-in doesn't open | Try running the script again; check your browser isn't blocking popups |
| No contacts returned | Check that your Search Objective and Search Rules tabs exist in the Google Doc and have content |
| Wrong sheet tab | Check that your Search Objective includes a line like `Sheet tab: Tab Name` |
