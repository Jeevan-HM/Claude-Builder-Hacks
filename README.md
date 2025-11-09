# 🚀 Claude Builder Hacks - AI-Powered Project Management

An intelligent team dashboard and project management system powered by AI, featuring automated task breakdown, smart team assignment, and interactive mindmap visualization.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)
![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-orange.svg)

## ✨ Features

### 🤖 AI-Powered Project Creation
- **PDF Document Analysis**: Upload project documents and let AI analyze and break them down
- **Intelligent Task Breakdown**: Claude AI generates 5-7 actionable tasks from project descriptions
- **Smart Team Assignment**: AI automatically assigns tasks based on team member skills and workload
- **Tech Stack Suggestions**: Get AI-recommended technology stacks for each task

### 📊 Team Dashboard
- **Interactive Project Cards**: Visual project management with drag-and-drop task assignment
- **Real-time Updates**: All changes sync instantly across dashboard and mindmap
- **Team Member Management**: Easy onboarding with editable profiles
- **Task Tracking**: Priority-based task management (High/Medium/Low)
- **Project Timeline**: Automated deadline calculation based on task complexity

### 🗺️ Visual Mindmap
- **Interactive Visualization**: See project structure in a connected mindmap view
- **Bidirectional Sync**: Changes in mindmap reflect in dashboard and vice versa
- **Entity Relationships**: Visualize connections between projects, teams, and tasks
- **Editable Nodes**: Update project/task/member details directly in the mindmap

### 🔧 Model Context Protocol (MCP) Integration
- **Git Operations**: Commit history, status, contributors analysis
- **Code Analysis**: Automated code quality checks and documentation generation
- **Task Decomposition**: Break down complex tasks into manageable subtasks
- **Time Estimation**: AI-powered task duration predictions
- **Testing Support**: Auto-generate test suites and code reviews

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vanilla JS)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Dashboard   │  │   Mindmap    │  │  Onboarding  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    Flask Backend (Python)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  REST API   │  Sync Engine  │  MCP Server           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│  AI Services              │           Database              │
│  ┌────────┐               │  ┌──────────────────────────┐  │
│  │ Claude │               │  │  SQLite (SQLAlchemy ORM) │  │
│  └────────┘               │  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Claude API Key (Anthropic)

### Installation

#### Option 1: Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/Jeevan-HM/Claude-Builder-Hacks.git
cd Claude-Builder-Hacks
```

2. **Create and activate virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install flask flask-sqlalchemy PyPDF2 flask-cors anthropic google-generativeai python-dotenv
```

Or using uv (faster):
```bash
uv pip install -r pyproject.toml
```

4. **Set up environment variables**
Create a `.env` file in the root directory:
```env
ANTHROPIC_API_KEY=your_claude_api_key_here
```

5. **Initialize the database**
```bash
python app.py
```
The database will be created automatically on first run.

6. **Access the application**
Open your browser and navigate to:
- Dashboard: http://localhost:5000
- Onboarding: http://localhost:5000/onboarding
- MCP Tester: http://localhost:5000/mcp-tester
- Mindmap: http://localhost:5000/mindmap

#### Option 2: Docker Setup

1. **Build the Docker image**
```bash
docker build -t claude-builder-hacks .
```

2. **Run the container**
```bash
docker run -d \
  -p 5000:5000 \
  -e ANTHROPIC_API_KEY=your_claude_api_key_here \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/project_tracker.db:/app/project_tracker.db \
  --name claude-builder \
  claude-builder-hacks
```

3. **Access the application**
Navigate to http://localhost:5000

### Docker Compose (Recommended)

Create a `docker-compose.yml` file:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./project_tracker.db:/app/project_tracker.db
    restart: unless-stopped
```

Then run:
```bash
docker-compose up -d
```

## 🌐 Deployment Options

### ✅ Recommended Platforms

#### 1. **Railway** (Best for this app)
Railway supports stateful applications with persistent storage:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```
- ✅ Supports file uploads
- ✅ Persistent storage (volumes)
- ✅ SQLite database works
- ✅ Environment variables
- ✅ Free tier available

#### 2. **Render**
Render supports Docker and persistent storage:
- ✅ Supports file uploads
- ✅ Persistent disks
- ✅ Auto-deploy from GitHub
- ✅ Free tier with limitations
- Create a `render.yaml` for easy deployment

#### 3. **DigitalOcean App Platform**
- ✅ Full Docker support
- ✅ Persistent storage
- ✅ Easy scaling
- 💰 Paid (starts at $5/month)

#### 4. **Fly.io**
- ✅ Excellent Docker support
- ✅ Persistent volumes
- ✅ Global deployment
- ✅ Generous free tier

#### 5. **Self-Hosted (VPS)**
Deploy on any VPS (AWS EC2, DigitalOcean Droplet, Linode, etc.):
```bash
# SSH into your server
ssh user@your-server.com

# Clone and run
git clone https://github.com/Jeevan-HM/Claude-Builder-Hacks.git
cd Claude-Builder-Hacks
./docker-start.sh
```
### 💡 Recommendation

**For easiest deployment with full functionality:** Use **Railway** or **Render**
- No code changes needed
- Supports all features
- Easy setup with Docker
- Affordable pricing

## 📖 Usage Guide

### Creating Your First Project

#### Method 1: AI-Assisted (Recommended)
1. Navigate to the Dashboard
2. Click "Create New Project"
3. Toggle "Use AI Assistant"
4. Upload a project document (PDF)
5. AI will analyze and create:
   - Project structure
   - Breakdown of 5-7 main tasks
   - Suggested priorities and deadlines
   - Smart team assignments

#### Method 2: Manual Creation
1. Click "Create New Project"
2. Enter project name and description
3. Choose a color tag
4. Add tasks manually using "Add Task"
5. Assign tasks to team members via drag-and-drop

### Managing Team Members

1. **Add Team Members**
   - Go to Onboarding page
   - Fill in name, role, and select avatar
   - Members appear in the dashboard sidebar

2. **Edit Member Details**
   - Click on member name or role in dashboard
   - Edit inline (changes sync to mindmap automatically)

3. **Assign Tasks**
   - Drag tasks from "Project Tasks" to team member cards
   - Or drag unassigned tasks directly to members

### Working with the Mindmap

1. **View Project Structure**
   - Navigate to Mindmap tab
   - See visual representation of projects, teams, and tasks

2. **Edit Nodes**
   - Click on any node to edit text
   - Changes sync back to dashboard automatically

3. **Navigate**
   - Zoom with mouse wheel
   - Pan by dragging canvas
   - Click "Fit View" to reset

### Using MCP Tools

Access developer productivity tools:
```python
# Available MCP Tools:
- git_commit_history: View commit history
- git_status: Check git status
- git_contributors: Analyze contributors
- analyze_code: Code quality analysis
- search_code: Search codebase
- generate_documentation: Auto-generate docs
- decompose_task: Break down complex tasks
- estimate_task_time: Estimate task duration
- generate_tests: Auto-generate test suites
- review_code: Code review assistance
- project_statistics: Project metrics
```

## 🗂️ Project Structure

```
Claude-Builder-Hacks/
├── app.py                      # Main Flask application
├── mcp_server/                 # Model Context Protocol server
│   ├── __init__.py
│   ├── server.py              # MCP server implementation
│   ├── flask_integration.py   # Flask Blueprint for MCP
│   └── config.json            # MCP configuration
├── static/                     # Frontend assets
│   └── team_dashboard.js      # Main dashboard logic
├── templates/                  # HTML templates
│   ├── team_dashboard.html    # Main dashboard UI
│   ├── mindmap.html           # Mindmap visualization
│   ├── onboarding.html        # Team onboarding
│   └── mcp_actions_tester.html # MCP testing interface
├── uploads/                    # PDF uploads directory
├── project_tracker.db          # SQLite database
├── .env                        # Environment variables
├── pyproject.toml             # Python dependencies
├── Dockerfile                 # Docker configuration
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude AI API key | Yes |
| `FLASK_ENV` | Flask environment (development/production) | No |
| `DATABASE_URL` | Database connection string | No (defaults to SQLite) |

### API Keys

Get your API key from:
- **Claude (Anthropic)**: https://console.anthropic.com/

## 🧪 Testing

Run the test suite:
```bash
python test_intelligent_assignment.py
```

Test MCP tools:
```bash
# Navigate to http://localhost:5000/mcp-tester
# Select a tool and test it interactively
```

## 🔒 Security Notes

- Never commit `.env` file with API keys
- Use environment variables for sensitive data
- Set appropriate file upload limits (default: 16MB)
- Validate and sanitize all user inputs
- Use HTTPS in production

## 📊 Database Schema

**Projects**: Stores project information
- id, name, tag_color, description, created_at

**TeamMembers**: Team member profiles
- id, name, role, avatar, avatar_color, created_at

**Tasks**: Project tasks
- id, title, priority, deadline, project_id, assigned_to, tech_stack

**ProjectMembers**: Many-to-many project-member assignments
- project_id, member_id, assigned_at

**Nodes**: Mindmap nodes
- id, x, y, text, level, entity_type, entity_id

**Connections**: Mindmap connections
- from_node, to_node

**MCPProjects**: AI-analyzed projects
- id, project_name, pdf_file, status, task_breakdown, mcp_analysis

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Known Issues & Limitations

- PDF text extraction quality depends on PDF structure
- AI task generation limited to 7 tasks (can be adjusted)
- SQLite not recommended for high-concurrency production use
- Mindmap performance may degrade with 100+ nodes

## 🔮 Roadmap

- [ ] Real-time collaboration with WebSockets
- [ ] Advanced analytics and reporting
- [ ] Integration with GitHub/GitLab
- [ ] Mobile-responsive design improvements
- [ ] Multi-language support
- [ ] Export projects to various formats (JSON, CSV, PDF)
- [ ] Calendar view for deadlines
- [ ] Notification system

## 📝 License

This project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)**. 

**You are free to:**
- Use the software for personal, educational, or non-commercial purposes
- Share and adapt the code with attribution

**You may NOT:**
- Use this software for commercial purposes
- Sell this software or derivative works
- Use it in commercial products or paid services

For commercial licensing inquiries, please contact the author.

See the [LICENSE](LICENSE) file for full details.

## 👤 Author

**Jeevan HM**
- GitHub: [@Jeevan-HM](https://github.com/Jeevan-HM)

## 🙏 Acknowledgments

- Claude AI by Anthropic for intelligent task generation
- Flask framework for backend simplicity
- Lucide Icons for beautiful UI icons

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation

---

**Made with ❤️ using AI and Python**
