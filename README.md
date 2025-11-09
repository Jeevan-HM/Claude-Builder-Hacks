# 🚀 Claude Builder Hacks - AI-Powered Project Management

A comprehensive project management system that combines **Claude AI** with **Model Context Protocol (MCP)** for intelligent task breakdown, analysis, and **automatic smart team assignment**.

## ✨ Key Features

### 🤖 **NEW: Intelligent Task Assignment with Claude MCP**
- **Automatically assigns tasks** to the best available team member using Claude AI
- Analyzes team member roles, current workload, task requirements, and priorities
- Provides transparent reasoning for each assignment decision
- Balances workload fairly across the team
- Matches skills to task requirements intelligently
- **[📖 Read Full Documentation](./INTELLIGENT_TASK_ASSIGNMENT.md)**

### 📄 **PDF Analysis & Task Generation**
- Upload project requirement PDFs
- AI-powered analysis and task breakdown
- Automatic project structure generation
- Detailed timeline and resource estimation

### 👥 **Team Management**
- Visual team dashboard with drag-and-drop
- Mindmap visualization of project structure
- Real-time task tracking
- Team member workload monitoring

### 🔄 **MCP Integration**
- Model Context Protocol for enhanced AI capabilities
- Git repository analysis
- Code analysis tools
- Project statistics and insights

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Jeevan-HM/Claude-Builder-Hacks.git
cd Claude-Builder-Hacks

# Install dependencies
pip install -r requirements.txt
# or
uv pip install -e .
```

### 2. Environment Setup

Create a `.env` file:

```bash
# Primary AI provider (Claude)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Fallback AI provider (optional)
GEMINI_API_KEY=...
```

### 3. Run the Application

```bash
python app.py
```

Visit `http://localhost:8000`

## 🎯 Usage

### Automatic Task Assignment

1. **Create a Project** - Upload a PDF with requirements
2. **AI Analysis** - Claude analyzes and generates tasks
3. **Auto-Assignment** - Tasks are intelligently assigned to team members
4. **View Dashboard** - See assignments with reasoning

### Manual Task Assignment

```bash
# Trigger auto-assignment for a project
curl -X POST http://localhost:8000/api/projects/{project_id}/auto-assign
```

**Response:**
```json
{
  "success": true,
  "assigned_by": "Claude AI",
  "assignments_made": 12,
  "assignments": [
    {
      "task_id": "task_1",
      "task_title": "Design authentication UI",
      "member_name": "Sarah Chen",
      "member_role": "Frontend Developer",
      "reasoning": "Frontend task matched to Frontend Developer with good capacity"
    }
  ]
}
```

## 🧪 Testing

Run the intelligent assignment test:

```bash
python test_intelligent_assignment.py
```

This will:
- Test the auto-assignment endpoint
- Verify task distribution
- Show detailed assignment reasoning
- Analyze workload balance

## 📊 Assignment Criteria

The AI considers multiple factors:

1. **Role Matching**
   - Frontend tasks → Frontend/Full Stack Developers
   - Backend tasks → Backend/Full Stack Developers
   - UI/UX tasks → Designers or Frontend Developers
   - Testing → QA Engineers
   - DevOps → DevOps Engineers or Backend Developers

2. **Workload Balancing**
   - Current task count per member
   - Fair distribution across team
   - Availability for urgent tasks

3. **Priority & Deadlines**
   - High priority → Experienced members
   - Urgent deadlines → Available members
   - Optimal timing consideration

## 📁 Project Structure

```
Claude-Builder-Hacks/
├── app.py                              # Main Flask application
├── mcp_server/                         # MCP integration
│   ├── server.py                       # MCP server implementation
│   └── flask_integration.py            # Flask MCP bridge
├── templates/                          # HTML templates
│   ├── team_dashboard.html            # Team dashboard
│   └── mcp_demo.html                  # MCP demo
├── static/                             # Frontend assets
│   └── team_dashboard.js              # Dashboard logic
├── INTELLIGENT_TASK_ASSIGNMENT.md     # Assignment docs
├── test_intelligent_assignment.py     # Test script
└── README.md                          # This file
```

## 🔧 API Endpoints

### Task Assignment
- `POST /api/projects/{id}/auto-assign` - Trigger intelligent assignment
- `PUT /api/tasks/{id}/assign` - Manual task assignment

### Project Management
- `GET /api/projects` - List all projects
- `POST /api/mcp-projects` - Create MCP project
- `POST /api/mcp-projects/{id}/analyze` - Analyze project PDF
- `POST /api/mcp-projects/{id}/create-dashboard-project` - Create with auto-assign

### Team Management
- `GET /api/team-members` - List team members
- `GET /api/tasks` - List all tasks
- `GET /api/mindmap` - Get mindmap visualization

## 🤖 AI Configuration

### Claude AI (Primary)
- Model: `claude-3-5-sonnet-20241022`
- Max tokens: 2048 (assignments), 4096 (task generation)
- Free tier: $5 credits

### Gemini AI (Fallback)
- Model: `gemini-2.0-flash-exp`
- Automatically used if Claude fails
- Free tier available

## 🎓 Best Practices

1. **Keep team roles accurate** - Ensure member roles reflect their expertise
2. **Add team members first** - Assign members to project before auto-assignment
3. **Review AI assignments** - Check reasoning and override if needed
4. **Balance team composition** - Include diverse roles for optimal matching
5. **Update workload** - Mark tasks complete to keep workload accurate

## 🔮 Roadmap

- [ ] Learn from manual overrides to improve assignments
- [ ] Consider member skill levels and experience
- [ ] Track task completion rates per member
- [ ] Predict task duration based on history
- [ ] Time zone considerations
- [ ] Calendar integration for availability
- [ ] Multi-project workload analysis

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines and submit PRs.

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- Built for the Claude AI Hackathon
- Powered by Anthropic's Claude AI
- Model Context Protocol integration
- Flask web framework

---

**Made with ❤️ for the Claude AI Hackathon** | [Documentation](./INTELLIGENT_TASK_ASSIGNMENT.md) | [Issues](https://github.com/Jeevan-HM/Claude-Builder-Hacks/issues)
