# GitHub Setup Guide

Your project is ready to push to GitHub! Follow these steps to connect your local repository to GitHub.

## Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `odds-api-project`
3. Description: `Data engineering pipeline for extracting Betway sports betting odds using The Odds API with Airflow orchestration and Databricks storage`
4. **Visibility**: Select **Private** (recommended for projects with sensitive configuration)
5. **DO NOT** initialize with README, .gitignore, or license (you already have these)
6. Click **Create Repository**

## Step 2: Add Remote and Push

Copy and run these commands in PowerShell from your project directory:

```powershell
cd c:\Users\Dell\Documents\Odds-API-Project\odds-api-project

git remote add origin https://github.com/lu-nomatye-profile/odds-api-project.git
git branch -M main
git push -u origin main
```

## Step 3: Verify Push

After running the push command, visit:
```
https://github.com/lu-nomatye-profile/odds-api-project
```

You should see:
- ✅ 7 files committed
- ✅ README.md displayed
- ✅ No sensitive data visible
- ✅ .env file NOT in repository

## What's Protected in Your Repository

### ✅ NOT Committed (Your .gitignore is protecting these):
- `.env` - Your actual API keys and credentials
- `venv/` - Python virtual environment
- `data/raw/*.csv` - Extracted data files
- `__pycache__/` - Compiled Python files
- `airflow/logs/` - Airflow logs
- `dbt/target/` - dbt build artifacts
- `.databrickscfg` - Databricks credentials

### ✅ Committed (Safe to share):
- `.env.example` - Template showing what variables are needed
- `README.md` - Complete project documentation
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Docker configuration
- `scripts/` - All Python source code
- `.gitignore` - Security rules

## If You Get an Authentication Error

If you see: `fatal: Authentication failed`

### Option A: Use GitHub Personal Access Token (Recommended)

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name it: `odds-api-project-push`
4. Select scopes: `repo` (full control of private repositories)
5. Click "Generate token"
6. Copy the token (you won't see it again!)

Then run:
```powershell
git remote set-url origin https://YOUR_TOKEN@github.com/lu-nomatye-profile/odds-api-project.git
git push -u origin main
```

Replace `YOUR_TOKEN` with your actual token.

### Option B: Use SSH (More Secure)

If you have SSH key configured:
```powershell
git remote set-url origin git@github.com:lu-nomatye-profile/odds-api-project.git
git push -u origin main
```

## After First Push: Future Commits

Once your remote is set up, future commits are simple:

```powershell
git add .
git commit -m "Your commit message here"
git push
```

## What to Commit Next

As you build out the project, commit code for:

1. **Phase 4**: Airflow DAG files (when created)
2. **Phase 5**: dbt transformation models (when created)
3. **Phase 6**: Additional scripts and configurations

**Never commit:**
- `.env` files with real credentials
- API keys or tokens
- Database passwords
- Personal data files

## Example: Committing After Adding Airflow DAG

```powershell
# After creating airflow/dags/odds_pipeline.py
git add airflow/dags/odds_pipeline.py
git commit -m "Add: Main Airflow DAG for odds extraction pipeline

- Extract odds every 6 hours
- Support multiple sports and bookmakers
- Error handling and retry logic
- XCom for task communication"
git push
```

## Repository Settings (Optional Enhancements)

After creating your repository, consider:

1. **Branch Protection** (Settings → Branches):
   - Require pull request reviews
   - Require status checks to pass

2. **Secrets Management** (Settings → Secrets and variables):
   - Store ODDS_API_KEY as repository secret
   - Use in GitHub Actions when needed

3. **README on Profile**:
   - Add link to this project in your GitHub profile bio

## Troubleshooting

### "Repository already exists"
You may have already created it. Check https://github.com/lu-nomatye-profile/odds-api-project

### "fatal: not a git repository"
Run from the project root:
```powershell
cd c:\Users\Dell\Documents\Odds-API-Project\odds-api-project
```

### "Your branch is ahead of origin/main by X commits"
This is normal after push. It means everything is uploaded. You're good to go!

---

## Next Steps After GitHub Setup

1. ✅ Push initial commit
2. 🔄 Update remote URL if needed
3. 📝 Continue development on Phase 4 (Docker/Airflow)
4. 🔄 Commit progress regularly with meaningful messages

Good luck! 🚀
