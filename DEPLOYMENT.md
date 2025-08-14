# Streamlit Cloud Deployment Guide

## Files Ready for Deployment

✅ **Core Application Files:**
- `app.py` - Main Streamlit application
- `enhanced_historian.py` - AI historian analysis
- `enhanced_speaker_parser.py` - Speaker identification
- `enhanced_framing.py` - Advanced framing system
- `hansard_simple.db` - Database with 430+ quotes

✅ **Configuration Files:**
- `requirements.txt` - Python dependencies
- `.streamlit/config.toml` - Streamlit theme settings
- `.gitignore` - Excludes unnecessary files
- `README.md` - Project documentation

## Step-by-Step Deployment

### 1. Create GitHub Repository
1. Go to https://github.com and create a new repository
2. Name it something like `hansard-quote-explorer`
3. Make it **public** (required for free Streamlit Cloud)
4. Don't initialize with README (we have our own)

### 2. Upload Files to GitHub
```bash
# In your project directory
git init
git add app.py enhanced_historian.py enhanced_speaker_parser.py enhanced_framing.py
git add hansard_simple.db requirements.txt README.md DEPLOYMENT.md
git add .streamlit/config.toml .gitignore
git commit -m "Initial deployment of Hansard Quote Explorer"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/hansard-quote-explorer.git
git push -u origin main
```

### 3. Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select your repository: `YOUR_USERNAME/hansard-quote-explorer`
5. Set main file path: `app.py`
6. Click "Deploy!"

### 4. Your App Will Be Live
- URL: `https://YOUR_USERNAME-hansard-quote-explorer-app-xxxxx.streamlit.app`
- Updates automatically when you push to GitHub
- Free hosting with reasonable limits

## File Sizes Check
- `hansard_simple.db`: ~2.3MB ✅ (under 100MB limit)
- Total repository: ~3MB ✅
- No large files that need Git LFS

## Features Included in Deployed Version
- 430+ parliamentary quotes (1900-1930)
- Enhanced framing with confidence scoring
- Clean academic interface
- CSV download functionality
- Historical analysis for each quote
- Quality filtering (confidence ≥ 5)
- Responsive design

## Sharing
Once deployed, anyone can access your research tool by visiting the URL. Perfect for:
- Academic collaborators
- Research presentations
- Sharing with supervisors
- Public access to your research

## Maintenance
- Database updates: Upload new `hansard_simple.db` to GitHub
- Code updates: Push changes to GitHub (auto-deploys)
- Monitor usage in Streamlit Cloud dashboard

---

**Next Steps:**
1. Create GitHub account if needed
2. Create new repository
3. Upload files
4. Deploy on Streamlit Cloud
5. Share the URL!

The system is ready for deployment with all dependencies resolved and optimized for cloud hosting.