# GitHub Commit Guide

## ✅ Security Check Complete

All sensitive information has been secured:
- ✅ `.env` file is properly ignored (contains real API keys)
- ✅ `.env.example` has placeholder values only
- ✅ No hardcoded API keys in code files

## Steps to Commit to GitHub

### Step 1: Initialize Git Repository (if not already done)

```bash
cd /Users/varunraste/Downloads/UI_Agentic
git init
```

### Step 2: Check What Will Be Committed

```bash
# See all files that will be committed
git status

# See only files in this directory (not parent)
git status --short | grep "^[^.]"
```

### Step 3: Add Files to Staging

```bash
# Add all files in current directory
git add .

# OR add specific files/folders
git add app/
git add streamlit_app.py
git add requirements.txt
git add README.md
git add .env.example
git add .gitignore
git add run_app.sh
```

### Step 4: Verify No Sensitive Files Are Included

```bash
# Double-check that .env is NOT being committed
git status | grep "\.env$" && echo "⚠️ WARNING: .env file is being tracked!" || echo "✅ .env is safely ignored"

# Check for any API keys in staged files
git diff --cached | grep -E "sk-|api_key.*=.*[A-Za-z0-9]{20,}" && echo "⚠️ WARNING: Possible API key found!" || echo "✅ No API keys in staged files"
```

### Step 5: Commit Changes

```bash
git commit -m "Initial commit: Agentic BFSI Document Intelligence Chatbot

Features:
- LangGraph-based agent orchestration
- KPI report generation
- Agentic RAG with tool integration
- Streamlit UI with execution time tracking
- KV-caching and speculative decoding support"
```

### Step 6: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., `bfsi-document-intelligence`)
3. **DO NOT** initialize with README, .gitignore, or license (we already have these)

### Step 7: Connect to GitHub and Push

```bash
# Add remote repository (replace with your GitHub username and repo name)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Rename branch to main if needed
git branch -M main

# Push to GitHub
git push -u origin main
```

## Important Security Reminders

### ✅ Safe to Commit:
- ✅ `.env.example` (has placeholder values)
- ✅ All Python code files
- ✅ `requirements.txt`
- ✅ `README.md`
- ✅ `.gitignore`
- ✅ `run_app.sh`
- ✅ Documentation files

### ❌ NEVER Commit:
- ❌ `.env` file (contains real API keys)
- ❌ `venv/` directory
- ❌ `vector_store/` directory (contains document data)
- ❌ `__pycache__/` directories
- ❌ Any files with real API keys or secrets

## If You Accidentally Committed Sensitive Data

If you accidentally committed `.env` or other sensitive files:

```bash
# Remove from git history (DANGEROUS - only if needed)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: This rewrites history)
git push origin --force --all
```

**Better approach:** Rotate/regenerate all API keys that were exposed!

## Final Checklist Before Pushing

- [ ] `.env` is in `.gitignore` ✅
- [ ] `.env.example` has no real keys ✅
- [ ] No API keys hardcoded in code ✅
- [ ] `venv/` is ignored ✅
- [ ] `vector_store/` is ignored ✅
- [ ] All sensitive files are ignored ✅
- [ ] Commit message is descriptive ✅

## Quick Commands Reference

```bash
# Check what will be committed
git status

# Add all files
git add .

# Commit
git commit -m "Your commit message"

# Push to GitHub
git push origin main

# Check for secrets before committing
git diff --cached | grep -i "api_key\|password\|secret\|token"
```

