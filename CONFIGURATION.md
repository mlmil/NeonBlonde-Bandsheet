# Neon Blonde Bandsheet — Configuration

All configuration for this project lives in **one place**: `config.json` in the root folder. You set it up once, then everything works automatically.

## config.json

This file contains all the settings the script needs:

```json
{
  "calendar_id": "neonblondevc@gmail.com",
  "drive_folder_id": "1ty5TilWvRixwobpkuHzigcluss0CTUl-",
  "credentials_file": "credentials.json",
  "google_workspace_account": "mike@neonblonde.com"
}
```

**Fields:**
- `calendar_id` — The Google Calendar to read gigs from (the public calendar)
- `drive_folder_id` — The Google Drive folder where receipt documents are saved
- `credentials_file` — Path to the credentials file (can be local or GitHub Actions secret)
- `google_workspace_account` — The Neon Blonde Google Workspace account (optional, for reference)

## Credentials Setup

The script needs credentials to create documents in Google Drive. You have two options:

### Option 1: Service Account (Recommended for GitHub Actions)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a service account with Drive API access
3. Download the JSON key file
4. Rename it to `credentials.json` and place it in the project root
5. Share the Drive folder (`drive_folder_id`) with the service account email
6. The script will automatically use it

### Option 2: OAuth User Credentials (Local Testing)

1. Use the existing `credentials.json` file if you already have OAuth credentials set up
2. The script will authenticate as the Neon Blonde workspace account
3. Make sure the account has access to the Drive folder

## GitHub Actions Secrets

When deploying to GitHub Actions:

1. Go to your repo **Settings → Secrets and variables → Actions**
2. Add secret `GOOGLE_CREDENTIALS_JSON` with the contents of your `credentials.json`
3. In the workflow, the script will read this and create the `credentials.json` file automatically

The workflow already handles this — just make sure the secret is named correctly.

## How It Works

1. **Daily at 2 PM UTC**, the GitHub Actions workflow runs
2. Script reads `config.json` to find the calendar and Drive folder
3. Fetches events from the Google Calendar
4. Generates the bandsheet JSON
5. Creates a receipt document in the Drive folder showing what was generated
6. Commits and pushes updates to GitHub

## Troubleshooting

**"No such file: config.json"**
- Make sure `config.json` exists in the project root with the correct structure

**"Permission denied" when creating receipt**
- The credentials need Drive API access
- The service account needs to be shared on the Drive folder
- Make sure `drive_folder_id` is correct

**Receipt doesn't appear in Drive**
- Check the script logs in GitHub Actions
- Verify the folder ID is correct
- Make sure credentials have permission to write to that folder

---

That's it. Everything lives in `config.json`. No more hunting for folder IDs.
