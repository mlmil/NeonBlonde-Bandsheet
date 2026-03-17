# Neon Blonde Band Sheet - GitHub Setup

## Overview

This repo automatically generates a Band Sheet from the Neon Blonde Google Calendar and publishes it to GitHub Pages. Updates happen daily at 6 AM PT.

## What You Need to Do

### 1. Create the GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `NeonBlonde-Bandsheet`
3. Description: "Neon Blonde band schedule and availability"
4. **Make it Public** (required for GitHub Pages to work with free account)
5. Click "Create repository"

### 2. Set Up GitHub Secrets

You need to store your OAuth token and client secrets as GitHub Secrets so the workflow can access them securely.

1. In your new repo, go to **Settings → Secrets and variables → Actions**
2. Click **"New repository secret"**

**Add secret #1: `NEON_TOKEN_JSON`**
- Name: `NEON_TOKEN_JSON`
- Value: Copy the entire contents of `/Users/studio_hub/.mcp-homes/neonblonde/.go-google-mcp/token.json`
- Click "Add secret"

**Add secret #2: `NEON_CLIENT_SECRETS_JSON`**
- Name: `NEON_CLIENT_SECRETS_JSON`
- Value: Copy the entire contents of `/Users/studio_hub/.mcp-homes/neonblonde/.go-google-mcp/client_secrets.json`
- Click "Add secret"

### 3. Push Files to GitHub

On your Mac:

```bash
cd '/Volumes/VADER/GitHub Repos/NeonBlonde-Bandsheet'

# Initialize git
git init
git branch -M main

# Create .gitignore
echo -e "*.pyc\n__pycache__/\n.DS_Store\nbandsheet-data.json" > .gitignore

# Commit all files
git add .
git commit -m "Initial commit: Band Sheet generator"

# Add remote (replace mlmil with your username)
git remote add origin https://github.com/mlmil/NeonBlonde-Bandsheet.git
git push -u origin main
```

### 4. Enable GitHub Pages

1. Go to your repo **Settings**
2. Scroll to **"Pages"** section
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/ (root)**
4. Click "Save"
5. GitHub will build the site — wait a minute or two
6. You'll see: "Your site is live at `https://mlmil.github.io/NeonBlonde-Bandsheet/`"

### 5. Test the Workflow

1. Go to **Actions** tab in your repo
2. Click **"Update Band Sheet"** workflow on the left
3. Click **"Run workflow"** button
4. Select "main" branch, click **"Run workflow"**
5. The workflow will start — it should complete in ~30 seconds
6. Check the live site: `https://mlmil.github.io/NeonBlonde-Bandsheet/`

## How It Works

- **Every day at 6 AM PT**, GitHub Actions automatically:
  1. Runs the Python script (`generate_bandsheet.py`)
  2. Fetches events from neonblondevc@gmail.com calendar
  3. Generates a Band Sheet JSON file (`bandsheet-data.json`)
  4. Commits and pushes the changes to GitHub
  5. GitHub Pages serves the updated HTML

- **The HTML file** (`index.html`) loads the JSON and displays it with styling
- **No secrets are exposed** — they're stored safely in GitHub Secrets

## Monitoring & Troubleshooting

### Check if the workflow ran

1. Go to **Actions** tab
2. Look for recent "Update Band Sheet" runs
3. Click on a run to see logs

### If the workflow fails

Click the failed workflow run and check the logs. Common issues:
- **Token expired**: The refresh token should auto-refresh, but if it fails, you may need to update the secret
- **Calendar API error**: Check that neonblondevc@gmail.com still has the calendar
- **Git push failed**: Unlikely, but would show in the logs

### Manual update

You can always click **"Run workflow"** in the Actions tab to manually trigger an update.

## Sharing the Band Sheet

Share the live URL with the band:
```
https://mlmil.github.io/NeonBlonde-Bandsheet/
```

Or create a short link using a service like bit.ly for easier sharing in GroupMe.

## Customizing

### Change the update time

Edit `.github/workflows/update-bandsheet.yml` and modify the cron schedule:
```yaml
- cron: '0 14 * * *'  # Change this line (UTC format)
```

Current: 14:00 UTC = 6 AM PDT (roughly)

### Style the HTML

Edit `index.html` to change colors, fonts, or layout in the `<style>` section.

---

**That's it!** The Band Sheet will now update every morning and be live on GitHub Pages.
