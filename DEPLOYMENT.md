# 🚂 Deploying to Railway - Step by Step Guide

Railway is the recommended platform for deploying Claude Builder Hacks because it supports:
- ✅ Persistent file storage (for PDF uploads)
- ✅ SQLite database persistence
- ✅ Docker containers
- ✅ Environment variables
- ✅ Free tier with $5 credit monthly

## Prerequisites

- GitHub account
- Railway account (sign up at https://railway.app)
- Your API keys (Claude and/or Gemini)

## Method 1: Deploy from GitHub (Recommended)

### Step 1: Prepare Your Repository

1. **Push your code to GitHub** (if not already done):
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main  # or 'dev' branch
```

2. **Ensure these files are in your repo**:
   - ✅ `Dockerfile`
   - ✅ `requirements.txt` or `pyproject.toml`
   - ✅ `.dockerignore`
   - ✅ `app.py`

### Step 2: Deploy on Railway

1. **Login to Railway**
   - Go to https://railway.app
   - Click "Login" and authenticate with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository: `Claude-Builder-Hacks`
   - Railway will auto-detect the Dockerfile

3. **Configure Environment Variables**
   - Click on your service
   - Go to "Variables" tab
   - Add these variables:
   ```
   ANTHROPIC_API_KEY=your_claude_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   FLASK_ENV=production
   ```

4. **Add Persistent Volume for Uploads**
   - Go to "Settings" tab
   - Scroll to "Volumes"
   - Click "Add Volume"
   - Mount Path: `/app/uploads`
   - Name: `uploads`
   
5. **Add Persistent Volume for Database**
   - Click "Add Volume" again
   - Mount Path: `/app/project_tracker.db`
   - Name: `database`

6. **Configure Port**
   - Railway should auto-detect port 5000
   - If not, go to Settings → Networking → Port: `5000`

7. **Deploy**
   - Railway will automatically build and deploy
   - Wait for build to complete (2-5 minutes)
   - You'll get a public URL like: `https://your-app.railway.app`

### Step 3: Verify Deployment

1. **Check Deployment Logs**
   - Click "Deployments" tab
   - View build logs to ensure no errors

2. **Test Your App**
   - Open the provided URL
   - Try creating a team member
   - Test uploading a PDF
   - Verify AI features work

## Method 2: Deploy with Railway CLI

### Step 1: Install Railway CLI

```bash
# macOS/Linux
curl -fsSL https://railway.app/install.sh | sh

# Or with npm
npm install -g @railway/cli

# Or with Homebrew
brew install railway
```

### Step 2: Login and Initialize

```bash
# Login to Railway
railway login

# Navigate to your project
cd Claude-Builder-Hacks

# Initialize Railway project
railway init

# Link to existing project or create new one
```

### Step 3: Set Environment Variables

```bash
# Set your API keys
railway variables set ANTHROPIC_API_KEY=your_key_here
railway variables set GEMINI_API_KEY=your_key_here
railway variables set FLASK_ENV=production
```

### Step 4: Deploy

```bash
# Deploy your application
railway up

# The app will build and deploy automatically
```

### Step 5: Get Your URL

```bash
# Get your deployment URL
railway open
```

## Configuration Tips

### Optimize for Railway

1. **Set Build Command** (if needed):
   - Settings → Build → Command: `docker build -t app .`

2. **Set Start Command** (if needed):
   - Settings → Deploy → Command: `python app.py`

3. **Health Check Path**:
   - Settings → Health Check → Path: `/`

4. **Environment**:
   - Recommended: Production
   - This enables optimizations

### Monitoring

1. **View Logs**:
   ```bash
   railway logs
   ```
   Or view in Railway dashboard → Deployments → Logs

2. **Check Metrics**:
   - Dashboard shows CPU, Memory, Network usage
   - Monitor costs in Settings → Usage

3. **Database Backup**:
   - Download your database periodically:
   ```bash
   railway run sqlite3 project_tracker.db .dump > backup.sql
   ```

## Troubleshooting

### Build Fails

**Issue**: Docker build fails
```bash
# Check build logs in Railway dashboard
# Common issues:
# 1. Missing dependencies in requirements.txt
# 2. Dockerfile errors
```

**Solution**:
```bash
# Test locally first
docker build -t test-app .
docker run -p 5000:5000 test-app
```

### App Crashes on Startup

**Issue**: App starts but crashes immediately

**Check**:
1. Environment variables are set correctly
2. Port is set to 5000
3. View logs for error messages

**Solution**:
```bash
# View logs
railway logs --tail 100
```

### File Uploads Don't Persist

**Issue**: PDF uploads disappear after restart

**Solution**: Ensure volume is mounted correctly
- Settings → Volumes → Check mount path is `/app/uploads`
- Verify volume exists and is attached

### Database Resets

**Issue**: Database data is lost

**Solution**: 
- Mount database as volume (not just directory)
- Mount path: `/app/project_tracker.db` (file, not directory)

### API Keys Not Working

**Issue**: AI features return errors

**Check**:
```bash
# Verify variables are set
railway variables

# Should show:
# ANTHROPIC_API_KEY=sk-...
# GEMINI_API_KEY=AI...
```

### Out of Memory

**Issue**: App crashes with memory errors

**Solution**:
- Upgrade to paid plan for more RAM
- Or optimize memory usage in code

## Cost Estimation

**Free Tier**:
- $5 credit per month
- Typically sufficient for:
  - Personal projects
  - Testing
  - Low traffic apps
  - ~500-1000 requests/day

**Usage includes**:
- Execution time
- Memory usage
- Network egress
- Storage (volumes)

**Monitoring Costs**:
```bash
# Check current usage
railway status

# View in dashboard
Settings → Usage → Current cycle
```

**Upgrade Plans**:
- Hobby: $5/month (then pay-as-you-go)
- Pro: $20/month (more included resources)

## Continuous Deployment

Railway automatically redeploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Railway will:
# 1. Detect the push
# 2. Build new Docker image
# 3. Deploy automatically
# 4. Zero-downtime deployment
```

To disable auto-deploy:
- Settings → Deploys → Auto-Deploy: OFF

## Custom Domain

### Step 1: Add Domain in Railway
1. Settings → Domains
2. Click "Add Domain"
3. Enter your domain: `yourdomain.com`

### Step 2: Configure DNS
Add these records in your domain registrar:

**For root domain**:
```
Type: A
Name: @
Value: [Railway provides this IP]
```

**For subdomain**:
```
Type: CNAME
Name: app (or your subdomain)
Value: [Railway provides this]
```

### Step 3: Enable HTTPS
- Railway automatically provisions SSL certificate
- Usually takes 5-10 minutes

## Best Practices

1. **Use Environment Variables**
   - Never hardcode API keys
   - Store sensitive data in Railway Variables

2. **Enable Health Checks**
   - Railway can auto-restart unhealthy services
   - Set health check path to `/`

3. **Monitor Usage**
   - Check dashboard regularly
   - Set up billing alerts

4. **Regular Backups**
   - Download database backups weekly
   - Store uploads backups externally

5. **Use Staging Environment**
   - Create separate Railway project for testing
   - Test changes before deploying to production

## Success Checklist

After deployment, verify:

- [ ] App is accessible via Railway URL
- [ ] Can create team members (database works)
- [ ] Can upload PDF (file storage works)
- [ ] AI features work (API keys configured)
- [ ] Uploads persist after restart (volume works)
- [ ] Database persists after restart (volume works)
- [ ] No errors in logs
- [ ] Health check passes

## Support

**Railway Issues**:
- Documentation: https://docs.railway.app
- Discord: https://discord.gg/railway
- Twitter: @railway

**App Issues**:
- GitHub Issues: https://github.com/Jeevan-HM/Claude-Builder-Hacks/issues

---

**🎉 Congratulations! Your app is now live on Railway!**

Share your deployment URL and start managing projects with AI! 🚀
