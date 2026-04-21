# Research Automation

This tool reads your search criteria from a Google Doc, uses AI with live web search to find real contacts (with verified emails), and writes them directly to your Google Sheet — ready for the email automation script to pick up.

---

## Step 1 — Download This Project

1. Open **Cursor**
2. Open the Terminal: **Terminal** → **New Terminal**
3. Paste this command and press Enter:

```
git clone https://github.com/lab-reb/Research-Automation.git
```

4. Navigate into the project folder:

```
cd Research-Automation
```

---

## Step 2 — Install Python Dependencies

In the same terminal, paste this and press Enter:

```
pip install anthropic google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dotenv
```

---

## Step 3 — Create Your .env File

In the Cursor terminal, paste this command (replace each value with your own):

```
python -c "
with open('.env', 'w') as f:
    f.write('ANTHROPIC_API_KEY=paste-your-anthropic-key-here\n')
    f.write('GOOGLE_SHEET_ID=paste-your-sheet-id-here\n')
    f.write('GOOGLE_DOC_ID=paste-your-doc-id-here\n')
"
```

Your `ANTHROPIC_API_KEY` is the same one you used for the email automation. Your Sheet ID and Doc ID are in the URLs of the shared links Rachel sent you — the long string of letters and numbers between `/d/` and `/edit`.

You can also copy your existing `.env` from the Email-Automation folder and add `GOOGLE_DOC_ID` to it.

---

## Step 4 — Copy Your credentials.json

Copy the `credentials.json` file from your `Email-Automation` folder into the `Research-Automation` folder — it's the same file.

---

## Step 5 — Run the Script

```
python research.py
```

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

Open the Google Doc Rachel shared with you and click the tabs at the top of the document. Changes take effect the next time you run the script — no code changes needed.

### Search Objective tab

Controls who to find and where to put the results:

- **Who to target** — e.g. "Find 20 university extension specialists in horticulture"
- **Which regions** — e.g. "Focus on the Southeast US"
- **Target sheet tab** — include a line like `Sheet tab: Southeast Horticulture` to control where results are written in your Google Sheet

### Search Rules tab

Sets the boundaries for what counts as a valid contact:

- **Institution type** — e.g. "Only include contacts at land-grant universities"
- **Role requirements** — e.g. "Must be an extension specialist or department head"
- **Things to exclude** — e.g. "Do not include graduate students"

**Tips:**
- Be specific — the more detail you give, the more targeted the results will be
- If the results don't look right, update the Search Objective or Search Rules and run the script again
- The script never overwrites existing rows, it only adds new ones

---

## Getting Updates

1. Open the Terminal in Cursor and navigate to the project folder:

```
cd Research-Automation
```

2. Run:

```
git pull
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Re-run the `pip install ...` command from Step 2 |
| `credentials.json not found` | Make sure you copied it from the Email-Automation folder |
| No contacts returned | Check that your Search Objective and Search Rules tabs exist in the Google Doc and have content |
| Wrong sheet tab | Check that your Search Objective includes a line like `Sheet tab: Tab Name` |
