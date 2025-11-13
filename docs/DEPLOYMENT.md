# Deployment Guide

## Deploying to Streamlit Community Cloud

Streamlit Community Cloud is the easiest and FREE way to deploy your dashboard as a live website.

### Prerequisites

- GitHub account (you already have this!)
- NASDAQ Data Link API key
- FRED API key (optional but recommended)

### Step-by-Step Deployment

#### 1. Go to Streamlit Community Cloud

Visit [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.

#### 2. Create New App

Click the **"New app"** button in the top-right corner.

#### 3. Configure Your App

Fill in the deployment settings:

- **Repository**: `jehantar/stock-portfolio-tracker`
- **Branch**: `main`
- **Main file path**: `src/dashboard.py`
- **App URL** (optional): Choose a custom subdomain

#### 4. Add Your API Keys as Secrets

**IMPORTANT**: Do NOT add your API keys to the repository!

1. Before clicking "Deploy", click on **"Advanced settings"**
2. In the **Secrets** section, paste your API keys in TOML format:

```toml
NASDAQ_DATA_LINK_API_KEY = "your_nasdaq_api_key_here"
FRED_API_KEY = "your_fred_api_key_here"
```

Replace `your_nasdaq_api_key_here` and `your_fred_api_key_here` with your actual API keys.

#### 5. Deploy!

Click **"Deploy"** and wait 2-3 minutes for your app to build and launch.

Your dashboard will be live at: `https://your-app-name.streamlit.app`

### Managing Your Deployed App

#### Update API Keys

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click on your app
3. Click the hamburger menu (⋮) → **Settings**
4. Go to the **Secrets** tab
5. Update your keys and click **Save**

#### Auto-Deploy on Git Push

Every time you push changes to the `main` branch on GitHub, Streamlit Cloud will automatically rebuild and redeploy your app!

#### View Logs

Click on **"Manage app"** → **Logs** to see real-time application logs and debug any issues.

### Security Best Practices

✅ **DO:**
- Keep API keys in Streamlit Cloud Secrets
- Keep `.env` in `.gitignore` (already configured)
- Use the secrets.toml.example as a template

❌ **DON'T:**
- Commit `.env` files to git
- Share your API keys publicly
- Hardcode API keys in source code

### Troubleshooting

**App won't start:**
- Check that your secrets are properly formatted (valid TOML)
- View the logs to see specific error messages
- Ensure all dependencies are in `requirements.txt`

**API errors:**
- Verify your NASDAQ API key is valid at [data.nasdaq.com](https://data.nasdaq.com)
- Check you haven't exceeded your API rate limits

**Slow performance:**
- First data fetch takes 30-60 seconds (normal)
- Data is cached for 1 hour after that
- Free tier has limited resources

### Alternative Deployment Options

If you want more control or need private hosting:

- **Heroku**: More configuration but more control
- **AWS EC2**: Full control, requires DevOps knowledge
- **DigitalOcean App Platform**: Balance of ease and control
- **Railway**: Similar to Heroku, modern platform

For most users, Streamlit Community Cloud is the best option!

---

**Need help?** Check the [Streamlit Community Forum](https://discuss.streamlit.io/) or the project's GitHub issues.
