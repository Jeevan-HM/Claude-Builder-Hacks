# 🧪 Testing Guide

## Quick Test - Docker

The fastest way to test the application:

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env and add your API keys

# 2. Run with Docker
./docker-start.sh
```

Then visit: http://localhost:5000

## Quick Test - Local

```bash
# 1. Run the quick start script
./start.sh
```

The script will:
- Create virtual environment
- Install dependencies
- Set up directories
- Start the server

## Manual Testing Steps

### 1. Initial Setup
```bash
# Clone the repository
git clone https://github.com/Jeevan-HM/Claude-Builder-Hacks.git
cd Claude-Builder-Hacks

# Set up environment
cp .env.example .env
nano .env  # Add your API keys

# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the app
python app.py
```

### 2. Test Onboarding (Add Team Members)
1. Navigate to http://localhost:5000/onboarding
2. Add a team member:
   - Name: "John Doe"
   - Role: "Full Stack Developer"
   - Select an avatar
   - Click "Add Team Member"
3. Add 2-3 more team members
4. Verify they appear in the list

### 3. Test Manual Project Creation
1. Go to http://localhost:5000 (Dashboard)
2. Click "Create New Project"
3. Enter project details:
   - Name: "E-commerce Platform"
   - Description: "Online shopping system"
   - Select a color
4. Click "Create Project"
5. Verify project appears in sidebar

### 4. Test Manual Task Creation
1. Select the project you created
2. Click "Add Task"
3. Create a task:
   - Title: "Design database schema"
   - Priority: High
   - Deadline: Pick a date
4. Click "Create Task"
5. Verify task appears in "Project Tasks"

### 5. Test Drag & Drop Assignment
1. Drag the task from "Project Tasks"
2. Drop it on a team member card
3. Verify task moves to member's "Assigned Tasks"
4. Check the task shows priority color

### 6. Test Inline Editing
1. Click on a team member's name
2. Edit the name inline
3. Press Enter
4. Verify the change is saved
5. Try editing the role as well

### 7. Test AI-Assisted Project Creation
1. Click "Create New Project"
2. Toggle "Use AI Assistant" ON
3. Prepare a PDF with project description
4. Upload the PDF
5. Wait for AI analysis (may take 10-30 seconds)
6. Verify:
   - Project is created
   - 5-7 tasks are generated
   - Tasks have priorities and deadlines
   - Success message appears

### 8. Test Mindmap Sync
1. Go to http://localhost:5000/mindmap
2. Verify your projects appear as nodes
3. Click on a project node
4. Edit the text
5. Go back to Dashboard
6. Verify the change reflected in project name

### 9. Test MCP Tools
1. Navigate to http://localhost:5000/mcp-tester
2. Select "git_status" tool
3. Enter repository path: "."
4. Click "Call Tool"
5. Verify git status is displayed
6. Try other tools (git_commit_history, analyze_code, etc.)

### 10. Test Task Deletion
1. In Dashboard, hover over a task
2. Click the delete icon
3. Confirm deletion
4. Verify task is removed

## Docker Testing

### Build and Test
```bash
# Build the image
docker build -t claude-builder-hacks .

# Run the container
docker run -d -p 5000:5000 \
  -e ANTHROPIC_API_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  --name test-builder \
  claude-builder-hacks

# Check logs
docker logs -f test-builder

# Access the app
open http://localhost:5000

# Clean up
docker stop test-builder
docker rm test-builder
```

### Docker Compose Testing
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

## API Testing

### Using curl

```bash
# Get all projects
curl http://localhost:5000/api/projects

# Get all team members
curl http://localhost:5000/api/team-members

# Create a project
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-project",
    "name": "Test Project",
    "tagColor": "blue",
    "description": "Testing API"
  }'

# Create a task
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-task-1",
    "title": "Test Task",
    "priority": "high",
    "deadline": "Dec 15",
    "projectId": "test-project"
  }'
```

### Using Python requests

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Get projects
response = requests.get(f"{BASE_URL}/projects")
print(response.json())

# Create team member
member_data = {
    "id": "test-member",
    "name": "Test User",
    "role": "Tester",
    "avatar": "🧪",
    "avatarColor": "blue"
}
response = requests.post(f"{BASE_URL}/team-members", json=member_data)
print(response.json())
```

## Performance Testing

### Load Test with Apache Bench
```bash
# Install Apache Bench (if not installed)
# macOS: brew install httpd
# Ubuntu: apt-get install apache2-utils

# Test dashboard endpoint
ab -n 100 -c 10 http://localhost:5000/

# Test API endpoint
ab -n 100 -c 10 http://localhost:5000/api/projects
```

## Common Issues & Solutions

### Issue: "Module not found"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Database is locked"
**Solution**: Close other connections or delete the .db file and restart

### Issue: "API key not found"
**Solution**: Check .env file has correct API keys

### Issue: "Port 5000 already in use"
**Solution**: 
```bash
# Find process using port 5000
lsof -i :5000
# Kill the process
kill -9 PID
```

### Issue: Docker build fails
**Solution**: 
```bash
# Clean up Docker
docker system prune -a
# Rebuild
docker build --no-cache -t claude-builder-hacks .
```

## Automated Testing

Run the test suite:
```bash
python test_intelligent_assignment.py
```

## Browser Testing

Test in multiple browsers:
- Chrome/Chromium
- Firefox
- Safari
- Edge

Verify:
- UI renders correctly
- Drag and drop works
- Icons display properly
- Responsive design (mobile view)

## Success Criteria

✅ All team members added successfully
✅ Projects created (manual and AI)
✅ Tasks created and assigned
✅ Drag and drop works smoothly
✅ Inline editing saves changes
✅ Mindmap syncs bidirectionally
✅ MCP tools execute successfully
✅ Docker container runs without errors
✅ No console errors in browser
✅ Database persists across restarts

---

**Happy Testing! 🚀**
