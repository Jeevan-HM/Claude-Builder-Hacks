import json
import os
from datetime import datetime, timedelta

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)

# Initialize Claude (Anthropic) client with fallback to Gemini
try:
    anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    USE_CLAUDE = True
except Exception:
    anthropic_client = None
    USE_CLAUDE = False

# Initialize Gemini as fallback
try:
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    USE_GEMINI = True
except Exception:
    USE_GEMINI = False

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "project_tracker.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# File upload configuration
UPLOAD_FOLDER = os.path.join(basedir, "uploads")
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# Register MCP Blueprint
from mcp_server.flask_integration import mcp_bp

app.register_blueprint(mcp_bp)

# ==================== DATABASE MODELS ====================


class Node(db.Model):
    __tablename__ = "nodes"

    id = db.Column(db.Integer, primary_key=True)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    text = db.Column(db.String(500), nullable=False)
    level = db.Column(db.Integer, nullable=False, default=0)
    entity_type = db.Column(
        db.String(50), nullable=True
    )  # 'project', 'team', 'member', 'task'
    entity_id = db.Column(
        db.String(100), nullable=True
    )  # Reference to project/member/task ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "text": self.text,
            "level": self.level,
            "entityType": self.entity_type,
            "entityId": self.entity_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Connection(db.Model):
    __tablename__ = "connections"

    id = db.Column(db.Integer, primary_key=True)
    from_node = db.Column(
        db.Integer, db.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    to_node = db.Column(
        db.Integer, db.ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "from": self.from_node,
            "to": self.to_node,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TeamMember(db.Model):
    __tablename__ = "team_members"

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(10), nullable=False)
    avatar_color = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "avatar": self.avatar,
            "avatarColor": self.avatar_color,
        }


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    tag_color = db.Column(db.String(20), nullable=False, default="blue")
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "tagColor": self.tag_color,
            "description": self.description,
        }


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="medium")
    deadline = db.Column(db.String(20), nullable=False)
    project_id = db.Column(
        db.String(50), db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    assigned_to = db.Column(
        db.String(50),
        db.ForeignKey("team_members.id", ondelete="SET NULL"),
        nullable=True,
    )
    tech_stack = db.Column(
        db.Text, nullable=True
    )  # JSON string of suggested tech stack
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "deadline": self.deadline,
            "projectId": self.project_id,
            "assignedTo": self.assigned_to,
            "techStack": json.loads(self.tech_stack) if self.tech_stack else None,
        }


class ProjectMember(db.Model):
    __tablename__ = "project_members"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(
        db.String(50), db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    member_id = db.Column(
        db.String(50),
        db.ForeignKey("team_members.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        db.UniqueConstraint("project_id", "member_id", name="unique_project_member"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "projectId": self.project_id,
            "memberId": self.member_id,
            "assignedAt": self.assigned_at.isoformat() if self.assigned_at else None,
        }


class MCPProject(db.Model):
    """MCP-enhanced project with PDF and analysis"""

    __tablename__ = "mcp_projects"

    id = db.Column(db.String(50), primary_key=True)
    project_name = db.Column(db.String(200), nullable=False)
    pdf_filename = db.Column(db.String(500), nullable=True)
    pdf_text_content = db.Column(db.Text, nullable=True)
    mcp_analysis = db.Column(db.Text, nullable=True)  # JSON string
    git_status = db.Column(db.Text, nullable=True)  # JSON string
    task_breakdown = db.Column(db.Text, nullable=True)  # JSON string
    time_estimates = db.Column(db.Text, nullable=True)  # JSON string
    code_summary = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(50), default="pending"
    )  # pending, processing, completed, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "projectName": self.project_name,
            "pdfFilename": self.pdf_filename,
            "pdfTextContent": self.pdf_text_content,
            "mcpAnalysis": json.loads(self.mcp_analysis) if self.mcp_analysis else None,
            "gitStatus": json.loads(self.git_status) if self.git_status else None,
            "taskBreakdown": json.loads(self.task_breakdown)
            if self.task_breakdown
            else None,
            "timeEstimates": json.loads(self.time_estimates)
            if self.time_estimates
            else None,
            "codeSummary": self.code_summary,
            "status": self.status,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


def allowed_file(filename):
    """Check if file has allowed extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== HELPER FUNCTIONS ====================


def generate_tech_stack_async(
    task_id, project_id, task_title, priority, deadline, assignee_id
):
    """
    Generate tech stack suggestions asynchronously in a background thread
    """
    with app.app_context():
        try:
            task = Task.query.get(task_id)
            if not task:
                print(f"Task {task_id} not found")
                return

            # Get project context
            project = Project.query.get(project_id)

            # Get assigned member info
            member_info = ""
            if assignee_id:
                member = TeamMember.query.get(assignee_id)
                if member:
                    member_info = f"Assigned to: {member.name} ({member.role})"

            prompt = f"""You are a technical architect helping a developer solve their task. 
    
Project: {project.name if project else "Unknown"}
Task: {task_title}
Priority: {priority}
Deadline: {deadline}
{member_info}

Based on this task, suggest:
1. **Tech Stack**: Specific technologies, frameworks, and libraries that would be best suited
2. **Tools**: Development tools, IDEs, or utilities that would help
3. **Best Practices**: Key architectural patterns or approaches to follow
4. **Resources**: 2-3 helpful documentation links or tutorials

Keep suggestions practical, modern, and specific to the task. Consider the priority and deadline.

Return a JSON object in this exact format:
{{
    "techStack": [
        {{"name": "Technology Name", "purpose": "Why it's recommended", "category": "frontend/backend/database/etc"}}
    ],
    "tools": [
        {{"name": "Tool Name", "purpose": "What it helps with"}}
    ],
    "bestPractices": [
        "Practice 1",
        "Practice 2",
        "Practice 3"
    ],
    "resources": [
        {{"title": "Resource Title", "url": "https://...", "description": "Brief description"}}
    ]
}}

IMPORTANT: Return ONLY the JSON object, no additional text or markdown."""

            ai_provider = None
            response_text = None

            # Try Claude first
            if USE_CLAUDE and anthropic_client:
                try:
                    message = anthropic_client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=2048,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    response_text = message.content[0].text.strip()
                    ai_provider = "Claude AI"
                    print(f"Tech stack generated by Claude for task {task_id}")
                except Exception as claude_error:
                    print(f"Claude API failed for task {task_id}: {claude_error}")
                    # Fall back to Gemini
                    if USE_GEMINI:
                        print(f"Falling back to Gemini for task {task_id}...")
                        model = genai.GenerativeModel("gemini-2.0-flash-exp")
                        response = model.generate_content(contents=prompt)
                        response_text = response.text.strip()
                        ai_provider = "Gemini AI (fallback)"
                        print(f"Tech stack generated by Gemini for task {task_id}")
                    else:
                        raise
            elif USE_GEMINI:
                model = genai.GenerativeModel("gemini-2.0-flash-exp")
                response = model.generate_content(contents=prompt)
                response_text = response.text.strip()
                ai_provider = "Gemini AI"
                print(f"Tech stack generated by Gemini for task {task_id}")
            else:
                print("No AI API available for tech stack generation")
                return

            # Parse response
            response_text = (
                response_text.strip()
                .removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )

            tech_stack_data = json.loads(response_text)

            # Save to database
            task.tech_stack = json.dumps(tech_stack_data)
            task.updated_at = datetime.utcnow()
            db.session.commit()

            print(f"✓ Tech stack saved for task {task_id} by {ai_provider}")

        except Exception as e:
            print(f"✗ Error generating tech stack for task {task_id}: {e}")


# ==================== ROUTES ====================


@app.route("/")
def index():
    return render_template("team_dashboard.html")


@app.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")


@app.route("/mindmap")
def mindmap():
    return render_template("mindmap.html")


@app.route("/mcp-workflow")
def mcp_workflow():
    return render_template("mcp_project_workflow.html")


# ==================== API ENDPOINTS ====================


# Get all nodes
@app.route("/api/nodes", methods=["GET"])
def get_nodes():
    nodes = Node.query.all()
    return jsonify([node.to_dict() for node in nodes])


# Create or update a node
@app.route("/api/nodes", methods=["POST"])
def create_or_update_node():
    data = request.json

    if "id" in data:
        node = Node.query.get(data["id"])
        if node:
            node.x = data.get("x", node.x)
            node.y = data.get("y", node.y)
            node.text = data.get("text", node.text)
            node.level = data.get("level", node.level)
            node.entity_type = data.get("entityType", node.entity_type)
            node.entity_id = data.get("entityId", node.entity_id)
            node.updated_at = datetime.utcnow()
        else:
            return jsonify({"error": "Node not found"}), 404
    else:
        node = Node(
            x=data["x"],
            y=data["y"],
            text=data["text"],
            level=data.get("level", 0),
            entity_type=data.get("entityType"),
            entity_id=data.get("entityId"),
        )
        db.session.add(node)

    db.session.commit()
    return jsonify(node.to_dict())


# Delete a node
@app.route("/api/nodes/<int:node_id>", methods=["DELETE"])
def delete_node(node_id):
    node = Node.query.get(node_id)
    if not node:
        return jsonify({"error": "Node not found"}), 404

    Connection.query.filter(
        (Connection.from_node == node_id) | (Connection.to_node == node_id)
    ).delete()

    db.session.delete(node)
    db.session.commit()
    return jsonify({"success": True})


# Get all connections
@app.route("/api/connections", methods=["GET"])
def get_connections():
    connections = Connection.query.all()
    return jsonify([conn.to_dict() for conn in connections])


# Create a connection
@app.route("/api/connections", methods=["POST"])
def create_connection():
    data = request.json

    existing = Connection.query.filter_by(
        from_node=data["from"], to_node=data["to"]
    ).first()

    if existing:
        return jsonify(existing.to_dict())

    connection = Connection(from_node=data["from"], to_node=data["to"])
    db.session.add(connection)
    db.session.commit()
    return jsonify(connection.to_dict())


# Delete connection by nodes
@app.route("/api/connections/by-nodes", methods=["DELETE"])
def delete_connection_by_nodes():
    data = request.json
    connection = Connection.query.filter_by(
        from_node=data["from"], to_node=data["to"]
    ).first()

    if not connection:
        return jsonify({"error": "Connection not found"}), 404

    db.session.delete(connection)
    db.session.commit()
    return jsonify({"success": True})


# Clear all data
@app.route("/api/clear-all", methods=["DELETE"])
def clear_all():
    try:
        Connection.query.delete()
        Node.query.delete()
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Get all team members
@app.route("/api/team-members", methods=["GET"])
def get_team_members():
    members = TeamMember.query.all()
    return jsonify([member.to_dict() for member in members])


# Create or update team member
@app.route("/api/team-members", methods=["POST"])
def create_or_update_team_member():
    data = request.json
    member = TeamMember.query.get(data["id"])

    if member:
        member.name = data.get("name", member.name)
        member.role = data.get("role", member.role)
        member.avatar = data.get("avatar", member.avatar)
        member.avatar_color = data.get("avatarColor", member.avatar_color)
    else:
        member = TeamMember(
            id=data["id"],
            name=data["name"],
            role=data["role"],
            avatar=data["avatar"],
            avatar_color=data["avatarColor"],
        )
        db.session.add(member)

    db.session.commit()
    return jsonify(member.to_dict())


# Delete team member
@app.route("/api/team-members/<string:member_id>", methods=["DELETE"])
def delete_team_member(member_id):
    member = TeamMember.query.get(member_id)

    if not member:
        return jsonify({"error": "Team member not found"}), 404

    # Delete all task assignments for this member
    Task.query.filter_by(assigned_to=member_id).update({"assigned_to": None})

    # Delete all project assignments for this member
    ProjectMember.query.filter_by(member_id=member_id).delete()

    # Delete the member
    db.session.delete(member)
    db.session.commit()

    return jsonify({"success": True})


# Get all projects with onboarding status
@app.route("/api/projects", methods=["GET"])
def get_projects():
    projects = Project.query.all()
    result = []
    for project in projects:
        project_dict = project.to_dict()
        project_dict["tasks"] = [
            task.to_dict() for task in Task.query.filter_by(project_id=project.id).all()
        ]
        # Add team members assigned to this project
        project_members = ProjectMember.query.filter_by(project_id=project.id).all()
        project_dict["teamMembers"] = [pm.member_id for pm in project_members]
        result.append(project_dict)
    return jsonify(result)


# Assign member to project
@app.route("/api/projects/<string:project_id>/members", methods=["POST"])
def assign_member_to_project(project_id):
    data = request.json
    member_id = data.get("memberId")

    if not member_id:
        return jsonify({"error": "memberId is required"}), 400

    # Check if project and member exist
    project = Project.query.get(project_id)
    member = TeamMember.query.get(member_id)

    if not project:
        return jsonify({"error": "Project not found"}), 404
    if not member:
        return jsonify({"error": "Member not found"}), 404

    # Check if already assigned
    existing = ProjectMember.query.filter_by(
        project_id=project_id, member_id=member_id
    ).first()

    if existing:
        return jsonify(
            {"message": "Member already assigned", "data": existing.to_dict()}
        )

    # Create new assignment
    project_member = ProjectMember(project_id=project_id, member_id=member_id)
    db.session.add(project_member)
    db.session.commit()

    return jsonify({"success": True, "data": project_member.to_dict()})


# Remove member from project
@app.route(
    "/api/projects/<string:project_id>/members/<string:member_id>", methods=["DELETE"]
)
def remove_member_from_project(project_id, member_id):
    project_member = ProjectMember.query.filter_by(
        project_id=project_id, member_id=member_id
    ).first()

    if not project_member:
        return jsonify({"error": "Assignment not found"}), 404

    db.session.delete(project_member)
    db.session.commit()

    return jsonify({"success": True})


# Get all members assigned to a project
@app.route("/api/projects/<string:project_id>/members", methods=["GET"])
def get_project_members(project_id):
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    project_members = ProjectMember.query.filter_by(project_id=project_id).all()
    member_ids = [pm.member_id for pm in project_members]

    members = [
        member.to_dict()
        for member in TeamMember.query.filter(TeamMember.id.in_(member_ids)).all()
    ]

    return jsonify(members)


# Create or update project
@app.route("/api/projects", methods=["POST"])
def create_or_update_project():
    data = request.json
    project = Project.query.get(data["id"])

    if project:
        project.name = data.get("name", project.name)
        project.tag_color = data.get("tagColor", project.tag_color)
        project.description = data.get("description", project.description)
    else:
        project = Project(
            id=data["id"],
            name=data["name"],
            tag_color=data.get("tagColor", "blue"),
            description=data.get("description", ""),
        )
        db.session.add(project)

    db.session.commit()

    # Trigger mindmap sync after project update
    sync_mindmap_internal()

    return jsonify(project.to_dict())


# Delete project
@app.route("/api/projects/<string:project_id>", methods=["DELETE"])
def delete_project(project_id):
    project = Project.query.get(project_id)

    if not project:
        return jsonify({"error": "Project not found"}), 404

    # Delete all tasks associated with this project (cascade should handle this, but being explicit)
    Task.query.filter_by(project_id=project_id).delete()

    # Delete all project member assignments
    ProjectMember.query.filter_by(project_id=project_id).delete()

    # Delete the project
    db.session.delete(project)
    db.session.commit()

    # Trigger mindmap sync after project deletion
    sync_mindmap_internal()

    return jsonify({"success": True})


# Create or update task
@app.route("/api/tasks", methods=["POST"])
def create_or_update_task():
    data = request.json
    task = Task.query.get(data["id"])

    if task:
        task.title = data.get("title", task.title)
        task.priority = data.get("priority", task.priority)
        task.deadline = data.get("deadline", task.deadline)
        task.project_id = data.get("projectId", task.project_id)
        task.assigned_to = data.get("assignedTo", task.assigned_to)
        task.updated_at = datetime.utcnow()
    else:
        task = Task(
            id=data["id"],
            title=data["title"],
            priority=data.get("priority", "medium"),
            deadline=data["deadline"],
            project_id=data["projectId"],
            assigned_to=data.get("assignedTo"),
        )
        db.session.add(task)

    db.session.commit()

    # Trigger mindmap sync after task update
    sync_mindmap_internal()

    return jsonify(task.to_dict())


# Delete task
@app.route("/api/tasks/<string:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    db.session.delete(task)
    db.session.commit()

    # Trigger mindmap sync after task deletion
    sync_mindmap_internal()

    return jsonify({"success": True})


# Assign/Unassign task
@app.route("/api/tasks/<string:task_id>/assign", methods=["PUT"])
def assign_task(task_id):
    data = request.json
    task = Task.query.get(task_id)

    if not task:
        return jsonify({"error": "Task not found"}), 404

    old_assignee = task.assigned_to
    new_assignee = data.get("assignedTo")

    task.assigned_to = new_assignee
    task.updated_at = datetime.utcnow()
    db.session.commit()

    # Auto-generate tech stack when task is assigned (not unassigned)
    if new_assignee and not old_assignee:
        try:
            # Generate tech stack asynchronously (in background)
            import threading

            thread = threading.Thread(
                target=generate_tech_stack_async,
                args=(
                    task_id,
                    task.project_id,
                    task.title,
                    task.priority,
                    task.deadline,
                    new_assignee,
                ),
            )
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"Error starting tech stack generation thread: {e}")

    # Trigger mindmap sync after assignment change
    sync_mindmap_internal()

    return jsonify(task.to_dict())


# Suggest tech stack for a task using AI
@app.route("/api/tasks/<string:task_id>/suggest-tech-stack", methods=["POST"])
def suggest_tech_stack(task_id):
    """
    Use Claude AI to suggest appropriate tech stack and tools for a task
    """
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    # Get project context
    project = Project.query.get(task.project_id)

    # Get assigned member info if available
    member_info = ""
    if task.assigned_to:
        member = TeamMember.query.get(task.assigned_to)
        if member:
            member_info = f"Assigned to: {member.name} ({member.role})"

    prompt = f"""You are a technical architect helping a developer solve their task. 
    
Project: {project.name}
Task: {task.title}
Priority: {task.priority}
Deadline: {task.deadline}
{member_info}

Based on this task, suggest:
1. **Tech Stack**: Specific technologies, frameworks, and libraries that would be best suited
2. **Tools**: Development tools, IDEs, or utilities that would help
3. **Best Practices**: Key architectural patterns or approaches to follow
4. **Resources**: 2-3 helpful documentation links or tutorials

Keep suggestions practical, modern, and specific to the task. Consider the priority and deadline.

Return a JSON object in this exact format:
{{
    "techStack": [
        {{"name": "Technology Name", "purpose": "Why it's recommended", "category": "frontend/backend/database/etc"}}
    ],
    "tools": [
        {{"name": "Tool Name", "purpose": "What it helps with"}}
    ],
    "bestPractices": [
        "Practice 1",
        "Practice 2",
        "Practice 3"
    ],
    "resources": [
        {{"title": "Resource Title", "url": "https://...", "description": "Brief description"}}
    ]
}}

IMPORTANT: Return ONLY the JSON object, no additional text or markdown."""

    try:
        ai_provider = None
        response_text = None

        # Try Claude first
        if USE_CLAUDE and anthropic_client:
            try:
                message = anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}],
                )
                response_text = message.content[0].text.strip()
                ai_provider = "Claude AI"
            except Exception as claude_error:
                print(f"Claude API failed: {claude_error}")
                # Fall back to Gemini
                if USE_GEMINI:
                    print("Falling back to Gemini...")
                    model = genai.GenerativeModel("gemini-2.0-flash-exp")
                    response = model.generate_content(contents=prompt)
                    response_text = response.text.strip()
                    ai_provider = "Gemini AI (fallback)"
                else:
                    raise
        elif USE_GEMINI:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            response = model.generate_content(contents=prompt)
            response_text = response.text.strip()
            ai_provider = "Gemini AI"
        else:
            return jsonify({"error": "No AI API available"}), 500

        # Parse response
        response_text = (
            response_text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

        tech_stack_data = json.loads(response_text)

        # Save to database
        task.tech_stack = json.dumps(tech_stack_data)
        task.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "taskId": task_id,
                "generatedBy": ai_provider,
                "techStack": tech_stack_data,
            }
        )

    except Exception as e:
        print(f"Error generating tech stack: {e}")
        return jsonify({"error": str(e)}), 500


# Smart Auto-Assign all unassigned tasks in a project using Claude MCP
@app.route("/api/projects/<string:project_id>/auto-assign", methods=["POST"])
def auto_assign_project_tasks(project_id):
    """
    Intelligently assign all unassigned tasks in a project to team members
    using Claude AI with MCP integration
    """
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    result = assign_tasks_intelligently_with_mcp(project_id)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


def sync_mindmap_internal():
    """Internal function to sync mindmap from team data"""
    try:
        # Clear existing nodes and connections
        Connection.query.delete()
        Node.query.delete()

        node_id_counter = 0
        node_map = {}

        projects = Project.query.all()

        if not projects:
            db.session.commit()
            return

        # Create nodes for each project
        for idx, project in enumerate(projects):
            project_node = Node(
                id=node_id_counter,
                x=150,
                y=250 + (idx * 450),
                text=f"{project.name}",
                level=0,
                entity_type="project",
                entity_id=project.id,
            )
            db.session.add(project_node)
            node_map[f"project_{project.id}"] = node_id_counter
            node_id_counter += 1

        # Create nodes for team members working on each project
        for idx, project in enumerate(projects):
            project_node_id = node_map[f"project_{project.id}"]

            tasks = Task.query.filter_by(project_id=project.id).all()
            assigned_member_ids = set(
                [task.assigned_to for task in tasks if task.assigned_to]
            )

            if not assigned_member_ids:
                continue

            # Create a team grouping node
            team_node_id = node_id_counter
            team_node = Node(
                id=team_node_id,
                x=550,
                y=250 + (idx * 450),
                text=f"Team Members",
                level=1,
                entity_type="team",
                entity_id=project.id,
            )
            db.session.add(team_node)

            conn = Connection(from_node=project_node_id, to_node=team_node_id)
            db.session.add(conn)
            node_id_counter += 1

            # Add individual member nodes
            member_y_start = 150 + (idx * 450)
            for member_idx, member_id in enumerate(sorted(assigned_member_ids)):
                member = TeamMember.query.get(member_id)
                if not member:
                    continue

                member_tasks = [t for t in tasks if t.assigned_to == member_id]

                member_node = Node(
                    id=node_id_counter,
                    x=950,
                    y=member_y_start + (member_idx * 90),
                    text=f"{member.name} - {member.role}",
                    level=2,
                    entity_type="member",
                    entity_id=member.id,
                )
                db.session.add(member_node)

                conn = Connection(from_node=team_node_id, to_node=node_id_counter)
                db.session.add(conn)

                member_node_id = node_id_counter
                node_id_counter += 1

                # Add task nodes for this member
                for task_idx, task in enumerate(member_tasks):
                    task_node = Node(
                        id=node_id_counter,
                        x=1350,
                        y=member_y_start + (member_idx * 90) + (task_idx * 60) - 20,
                        text=f"{task.title[:40]}{'...' if len(task.title) > 40 else ''}",
                        level=3,
                        entity_type="task",
                        entity_id=task.id,
                    )
                    db.session.add(task_node)

                    conn = Connection(from_node=member_node_id, to_node=node_id_counter)
                    db.session.add(conn)
                    node_id_counter += 1

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"Error syncing mindmap: {e}")


# Sync mindmap from team data (manual endpoint)
@app.route("/api/sync-mindmap", methods=["POST"])
def sync_mindmap():
    try:
        sync_mindmap_internal()
        return jsonify({"success": True, "message": "Mindmap synced from team data"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Initialize database
@app.route("/api/init-db", methods=["POST"])
def init_db():
    try:
        # Try to create all tables (will skip existing ones)
        db.create_all()

        # Try to migrate existing projects table if needed
        with db.engine.connect() as conn:
            # Check if description column exists
            result = conn.execute(db.text("PRAGMA table_info(projects)"))
            columns = [row[1] for row in result]

            if "description" not in columns:
                # Add description column to existing projects table
                conn.execute(
                    db.text("ALTER TABLE projects ADD COLUMN description TEXT")
                )
                conn.commit()

            # Check if entity_type and entity_id columns exist in nodes
            result = conn.execute(db.text("PRAGMA table_info(nodes)"))
            columns = [row[1] for row in result]

            if "entity_type" not in columns:
                conn.execute(
                    db.text("ALTER TABLE nodes ADD COLUMN entity_type VARCHAR(50)")
                )
                conn.commit()

            if "entity_id" not in columns:
                conn.execute(
                    db.text("ALTER TABLE nodes ADD COLUMN entity_id VARCHAR(100)")
                )
                conn.commit()
    except Exception as e:
        print(f"Migration warning: {e}")
        # If migration fails, continue anyway
        pass

    # Initialize team dashboard data
    if TeamMember.query.count() == 0:
        default_members = [
            TeamMember(
                id="tm1",
                name="Lucas Werner",
                role="Manager",
                avatar="LW",
                avatar_color="60a5fa",
            ),
            TeamMember(
                id="tm2",
                name="Priya Desai",
                role="Team Lead",
                avatar="PD",
                avatar_color="ec4899",
            ),
            TeamMember(
                id="tm3",
                name="Hao Nguyen",
                role="Principal Engineer",
                avatar="HN",
                avatar_color="f59e0b",
            ),
            TeamMember(
                id="tm4",
                name="Marta Kowalski",
                role="Senior Engineer",
                avatar="MK",
                avatar_color="8b5cf6",
            ),
            TeamMember(
                id="tm5",
                name="Diego Silva",
                role="Senior Engineer",
                avatar="DS",
                avatar_color="10b981",
            ),
            TeamMember(
                id="tm6",
                name="Ananya Rao",
                role="Associate Engineer",
                avatar="AR",
                avatar_color="ef4444",
            ),
            TeamMember(
                id="tm7",
                name="Ethan Brooks",
                role="Associate Engineer",
                avatar="EB",
                avatar_color="3b82f6",
            ),
            # === ADDED NEW MEMBERS ===
            TeamMember(
                id="tm8",
                name="Kenji Tanaka",
                role="DevOps Engineer",
                avatar="KT",
                avatar_color="22c55e",
            ),
            TeamMember(
                id="tm9",
                name="Sarah Chen",
                role="Hardware Engineer",
                avatar="SC",
                avatar_color="a855f7",
            ),
            TeamMember(
                id="tm10",
                name="David Kim",
                role="QA Engineer",
                avatar="DK",
                avatar_color="f43f5e",
            ),
            TeamMember(
                id="tm11",
                name="Chloé Dubois",
                role="UX/UI Designer",
                avatar="CD",
                avatar_color="14b8a6",
            ),
            TeamMember(
                id="tm12",
                name="Leon Vance",
                role="Data Scientist",
                avatar="LV",
                avatar_color="64748b",
            ),
        ]
        for member in default_members:
            db.session.add(member)

    if Project.query.count() == 0:
        # default_projects = [
        #     Project(
        #         id="vocalift",
        #         name="VocaLift (i18n Tool)",
        #         tag_color="yellow",
        #         description="Internationalization platform for seamless multi-language support across applications.",
        #     ),
        #     Project(
        #         id="authn-mfa",
        #         name="AuthN-MFA-Rollout",
        #         tag_color="green",
        #         description="Multi-factor authentication system rollout for enhanced security protocols.",
        #     ),
        #     Project(
        #         id="billing-v2",
        #         name="Billing-Orchestrator-v2",
        #         tag_color="blue",
        #         description="Next-generation billing infrastructure with improved scalability and performance.",
        #     ),
        # ]
        default_projects = []

        for project in default_projects:
            db.session.add(project)

    if Task.query.count() == 0:
        default_tasks = [
            Task(
                id="v-t1",
                title="Fix i18n string-loading bug",
                priority="low",
                deadline="Nov 10",
                project_id="vocalift",
                assigned_to="tm6",
            ),
            Task(
                id="v-t2",
                title="Implement new language pack (JP)",
                priority="low",
                deadline="Nov 14",
                project_id="vocalift",
                assigned_to=None,
            ),
            Task(
                id="v-t3",
                title="Audit translation key coverage",
                priority="medium",
                deadline="Nov 20",
                project_id="vocalift",
                assigned_to=None,
            ),
            Task(
                id="a-t1",
                title="Coordinating AuthN-MFA testing phase",
                priority="high",
                deadline="Nov 20",
                project_id="authn-mfa",
                assigned_to="tm2",
            ),
            Task(
                id="a-t2",
                title="Refactoring `identity-service` for MFA hooks",
                priority="high",
                deadline="Nov 18",
                project_id="authn-mfa",
                assigned_to="tm4",
            ),
            Task(
                id="a-t3",
                title="Adding new unit tests for `config-service` SDK",
                priority="low",
                deadline="Nov 12",
                project_id="authn-mfa",
                assigned_to="tm7",
            ),
            Task(
                id="a-t4",
                title="Update developer documentation for MFA",
                priority="medium",
                deadline="Nov 25",
                project_id="authn-mfa",
                assigned_to=None,
            ),
            Task(
                id="b-t1",
                title="Q4 planning & budget review for Billing-v2",
                priority="high",
                deadline="Nov 15",
                project_id="billing-v2",
                assigned_to="tm1",
            ),
            Task(
                id="b-t2",
                title="Designing service-mesh integration",
                priority="medium",
                deadline="Nov 22",
                project_id="billing-v2",
                assigned_to="tm3",
            ),
            Task(
                id="b-t3",
                title="Implementing new rate-limiting logic",
                priority="medium",
                deadline="Nov 25",
                project_id="billing-v2",
                assigned_to="tm5",
            ),
            Task(
                id="b-t4",
                title="Create new Grafana dashboards for billing",
                priority="low",
                deadline="Nov 28",
                project_id="billing-v2",
                assigned_to=None,
            ),
            Task(
                id="b-t5",
                title="Write integration tests for payment provider",
                priority="medium",
                deadline="Dec 02",
                project_id="billing-v2",
                assigned_to=None,
            ),
        ]

        for task in default_tasks:
            db.session.add(task)

    db.session.commit()

    # Sync mindmap after initialization
    sync_mindmap_internal()

    return jsonify({"success": True, "message": "Database initialized"})


# Database health check
@app.route("/api/health", methods=["GET"])
def health_check():
    try:
        node_count = Node.query.count()
        conn_count = Connection.query.count()
        member_count = TeamMember.query.count()
        project_count = Project.query.count()
        task_count = Task.query.count()
        return jsonify(
            {
                "status": "healthy",
                "mindmap": {"nodes": node_count, "connections": conn_count},
                "team": {
                    "members": member_count,
                    "projects": project_count,
                    "tasks": task_count,
                },
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# Reset database (use with caution)
@app.route("/api/reset-db", methods=["POST"])
def reset_db():
    """Complete database reset - drops and recreates all tables"""
    try:
        db.drop_all()
        db.create_all()
        return jsonify({"success": True, "message": "Database reset successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== MCP PROJECT WORKFLOW ENDPOINTS ====================


@app.route("/api/mcp-projects", methods=["GET"])
def get_mcp_projects():
    """Get all MCP projects"""
    projects = MCPProject.query.order_by(MCPProject.created_at.desc()).all()
    return jsonify([project.to_dict() for project in projects])


@app.route("/api/mcp-projects/<string:project_id>", methods=["GET"])
def get_mcp_project(project_id):
    """Get a specific MCP project"""
    project = MCPProject.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project.to_dict())


@app.route("/api/mcp-projects/create", methods=["POST"])
def create_mcp_project():
    """
    Create new MCP project with PDF upload and analysis

    Expected form data:
    - project_name: string
    - pdf_file: file (optional)
    """
    try:
        # Get project name from form data
        project_name = request.form.get("project_name")
        if not project_name:
            return jsonify({"error": "project_name is required"}), 400

        # Generate unique project ID
        project_id = f"mcp_{int(datetime.utcnow().timestamp() * 1000)}"

        # Handle PDF file upload
        pdf_filename = None
        pdf_text_content = None

        if "pdf_file" in request.files:
            pdf_file = request.files["pdf_file"]
            if pdf_file and pdf_file.filename and allowed_file(pdf_file.filename):
                filename = secure_filename(pdf_file.filename)
                # Add timestamp to avoid collisions
                filename = f"{project_id}_{filename}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                pdf_file.save(filepath)
                pdf_filename = filename

                # Analyze document with MCP
                try:
                    pdf_text_content = analyze_document_with_mcp(filepath)
                except Exception as e:
                    print(f"Error analyzing document: {e}")
                    pdf_text_content = f"Error analyzing document: {str(e)}"

        # Create project record
        project = MCPProject(
            id=project_id,
            project_name=project_name,
            pdf_filename=pdf_filename,
            pdf_text_content=pdf_text_content,
            status="pending",
        )

        db.session.add(project)
        db.session.commit()

        # Return initial project data
        return jsonify(
            {
                "success": True,
                "project": project.to_dict(),
                "message": "Project created successfully",
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/mcp-projects/<string:project_id>/analyze", methods=["POST"])
def analyze_mcp_project(project_id):
    """
    Analyze MCP project using Claude MCP

    This endpoint:
    1. Gets git status
    2. Analyzes code structure
    3. Breaks down tasks from PDF content
    4. Estimates time for tasks
    5. Generates code summary
    """
    try:
        project = MCPProject.query.get(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Update status to processing
        project.status = "processing"
        db.session.commit()

        # Import MCP functions
        from mcp_server.flask_integration import call_mcp_tool

        analysis_results = {}

        # 1. Get git status
        try:
            git_status = call_mcp_tool("git_status", {"repo_path": "."})
            analysis_results["gitStatus"] = git_status
            project.git_status = json.dumps(git_status)
        except Exception as e:
            analysis_results["gitStatus"] = {"error": str(e)}

        # 2. Analyze document with MCP and decompose tasks
        if project.pdf_text_content:
            try:
                # Parse the document metadata first
                doc_info = (
                    json.loads(project.pdf_text_content)
                    if project.pdf_text_content.startswith("{")
                    else {}
                )

                # Extract full content from document if available
                full_content = doc_info.get("full_content", "")
                content_preview = doc_info.get("content", "")

                print(f"DEBUG: Full content length: {len(full_content)}")
                print(f"DEBUG: Content preview (first 500 chars): {full_content[:500]}")

                # Use Claude AI to generate detailed task breakdown from PDF content
                if full_content:
                    print("DEBUG: Calling Claude API for task breakdown...")
                    task_breakdown = generate_task_breakdown_with_claude(
                        project.project_name, full_content
                    )
                    print(f"DEBUG: Claude task breakdown result: {task_breakdown}")
                else:
                    # Fallback if no content extracted
                    task_breakdown = {
                        "error": "No PDF content available for analysis",
                        "subtasks": [],
                        "total_subtasks": 0,
                    }

                analysis_results["taskBreakdown"] = task_breakdown
                project.task_breakdown = json.dumps(task_breakdown)

                # Store document info in analysis
                if doc_info:
                    analysis_results["documentInfo"] = doc_info
            except Exception as e:
                analysis_results["taskBreakdown"] = {"error": str(e)}

        # 3. Estimate time for main task
        try:
            time_estimate = call_mcp_tool(
                "estimate_task_time",
                {
                    "task_title": project.project_name,
                    "task_description": project.pdf_text_content[:500]
                    if project.pdf_text_content
                    else "",
                },
            )
            analysis_results["timeEstimate"] = time_estimate
            project.time_estimates = json.dumps(time_estimate)
        except Exception as e:
            analysis_results["timeEstimate"] = {"error": str(e)}

        # 4. Get project statistics
        try:
            project_stats = call_mcp_tool("project_statistics", {"directory": "."})
            analysis_results["projectStats"] = project_stats
        except Exception as e:
            analysis_results["projectStats"] = {"error": str(e)}

        # 5. Generate code summary
        code_summary = generate_code_summary(project, analysis_results)
        project.code_summary = code_summary
        analysis_results["codeSummary"] = code_summary

        # 6. Store complete MCP analysis
        project.mcp_analysis = json.dumps(analysis_results)
        project.status = "completed"
        project.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "project": project.to_dict(),
                "analysis": analysis_results,
            }
        )

    except Exception as e:
        if project:
            project.status = "error"
            project.mcp_analysis = json.dumps({"error": str(e)})
            db.session.commit()
        return jsonify({"error": str(e)}), 500


@app.route("/api/mcp-projects/<string:project_id>", methods=["DELETE"])
def delete_mcp_project(project_id):
    """Delete an MCP project and its associated files"""
    try:
        project = MCPProject.query.get(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Delete PDF file if exists
        if project.pdf_filename:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], project.pdf_filename)
            if os.path.exists(filepath):
                os.remove(filepath)

        db.session.delete(project)
        db.session.commit()

        return jsonify({"success": True, "message": "Project deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route(
    "/api/mcp-projects/<string:project_id>/create-dashboard-project", methods=["POST"]
)
def create_dashboard_project_from_mcp(project_id):
    """
    Create a Team Dashboard project from MCP analysis
    Uses Claude MCP to help structure Gemini output into actionable tasks
    """
    try:
        # Get MCP project
        mcp_project = MCPProject.query.get(project_id)
        if not mcp_project:
            return jsonify({"error": "MCP Project not found"}), 404

        if not mcp_project.task_breakdown:
            return jsonify(
                {
                    "error": "No task breakdown available. Please analyze the project first."
                }
            ), 400

        # Parse task breakdown
        task_breakdown = json.loads(mcp_project.task_breakdown)

        # Use Claude MCP to refine and structure the data
        from mcp_server.flask_integration import call_mcp_tool

        # Get project statistics to help with task assignment
        project_stats = call_mcp_tool("project_statistics", {"directory": "."})

        # Generate a unique project ID
        project_id_dashboard = f"mcp_{int(datetime.utcnow().timestamp() * 1000)}"

        # Determine project color based on complexity/priority
        tag_colors = ["blue", "green", "yellow", "purple", "pink", "red"]
        complexity = task_breakdown.get("timeline", {}).get("total_estimated_days", 0)
        if complexity > 30:
            tag_color = "red"  # High complexity
        elif complexity > 14:
            tag_color = "yellow"  # Medium complexity
        else:
            tag_color = "green"  # Low complexity

        # Create project description from Gemini analysis
        overview = task_breakdown.get("project_overview", {})
        objectives = overview.get("objectives", [])
        description = f"{overview.get('business_value', 'Project created from MCP analysis')}\n\nObjectives:\n"
        description += "\n".join(f"- {obj}" for obj in objectives[:3])

        # Create the project in Team Dashboard
        new_project = Project(
            id=project_id_dashboard,
            name=mcp_project.project_name,
            tag_color=tag_color,
            description=description[:500],  # Limit description length
        )
        db.session.add(new_project)

        # Get available team members
        team_members = TeamMember.query.all()

        if not team_members:
            return jsonify(
                {"error": "No team members available. Please add team members first."}
            ), 400

        # Create tasks from subtasks - leave unassigned for manual assignment
        subtasks = task_breakdown.get("subtasks", [])
        created_tasks = []

        for idx, subtask in enumerate(subtasks[:20]):  # Allow up to 20 tasks
            task_id = f"{project_id_dashboard}_task_{idx + 1}"

            # Map priority
            priority = subtask.get("priority", "medium").lower()
            if priority not in ["low", "medium", "high"]:
                priority = "medium"

            # Calculate deadline based on estimated hours
            estimated_hours = subtask.get("estimated_hours", 8)
            estimated_days = max(1, estimated_hours // 8)
            deadline_date = datetime.utcnow() + timedelta(
                days=estimated_days + (idx * 2)
            )
            deadline = deadline_date.strftime("%b %d")

            # Leave tasks unassigned so they appear in Project Tasks section
            # Users can drag-and-drop them to team members
            assigned_to = None

            # Create task
            task = Task(
                id=task_id,
                title=subtask.get("title", f"Task {idx + 1}"),
                priority=priority,
                deadline=deadline,
                project_id=project_id_dashboard,
                assigned_to=assigned_to,
            )
            db.session.add(task)
            created_tasks.append(task.to_dict())

        # Don't add team members to project yet - let the intelligent assignment do it
        # Only members who receive tasks will be added to the project

        # Link MCP project to dashboard project
        mcp_project.status = "deployed"
        mcp_analysis = (
            json.loads(mcp_project.mcp_analysis) if mcp_project.mcp_analysis else {}
        )
        mcp_analysis["dashboard_project_id"] = project_id_dashboard
        mcp_project.mcp_analysis = json.dumps(mcp_analysis)

        db.session.commit()

        # Sync mindmap
        sync_mindmap_internal()

        # Auto-assign tasks intelligently using Claude MCP
        assignment_result = assign_tasks_intelligently_with_mcp(project_id_dashboard)

        return jsonify(
            {
                "success": True,
                "message": "Dashboard project created successfully",
                "project": new_project.to_dict(),
                "tasks_created": len(created_tasks),
                "tasks": created_tasks,
                "auto_assignment": assignment_result,
                "dashboard_url": "/",
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Error creating dashboard project: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ==================== HELPER FUNCTIONS ====================


def assign_tasks_intelligently_with_mcp(project_id: str) -> dict:
    """
    Use Claude AI with MCP to intelligently assign tasks to team members
    Forms a team first, then allocates tasks based on importance and deadline
    """
    try:
        # Get all unassigned tasks for the project
        unassigned_tasks = Task.query.filter_by(
            project_id=project_id, assigned_to=None
        ).all()

        if not unassigned_tasks:
            return {"message": "No unassigned tasks found", "assignments": []}

        # Get ALL available team members (not just project members)
        all_team_members = TeamMember.query.all()

        if not all_team_members:
            return {"error": "No team members available in the system"}

        # Calculate current workload for each team member
        workload_data = []
        for member in all_team_members:
            current_tasks = Task.query.filter_by(
                project_id=project_id, assigned_to=member.id
            ).all()
            workload_data.append(
                {
                    "id": member.id,
                    "name": member.name,
                    "role": member.role,
                    "current_tasks": len(current_tasks),
                    "task_titles": [t.title for t in current_tasks],
                }
            )

        # Prepare task data for analysis - sort by priority and deadline
        task_data = []
        for task in unassigned_tasks:
            # Calculate priority score (high=3, medium=2, low=1)
            priority_score = {"high": 3, "medium": 2, "low": 1}.get(
                task.priority.lower(), 2
            )
            task_data.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "priority": task.priority,
                    "priority_score": priority_score,
                    "deadline": task.deadline,
                }
            )

        # Sort tasks by priority (high first) and then by deadline
        task_data.sort(key=lambda x: (-x["priority_score"], x["deadline"]))

        # Create prompt for Claude to form team and assign critical tasks
        prompt = f"""You are a project manager AI assistant. Analyze the tasks and team members, then:
1. Form an optimal team for this project (select only members who will receive tasks)
2. Assign only the most critical and urgent tasks (roughly 50-70% of tasks)
3. Leave some tasks unassigned for manual assignment by the project manager

AVAILABLE TEAM MEMBERS:
{json.dumps(workload_data, indent=2)}

UNASSIGNED TASKS (sorted by importance and deadline):
{json.dumps(task_data, indent=2)}

ASSIGNMENT CRITERIA:
1. Form a team: Select the minimum number of team members needed to cover all task types
2. Match task requirements with team member roles:
   - Frontend tasks → Frontend/Full Stack Developers
   - Backend/API tasks → Backend/Full Stack Developers  
   - UI/UX tasks → Designers or Frontend Developers
   - Testing tasks → QA Engineers or Full Stack Developers
   - DevOps/Infrastructure → DevOps Engineers or Backend Developers
   - Hardware tasks → Hardware Engineers
   - Data tasks → Data Scientists
3. Prioritize high-priority and urgent deadline tasks first
4. Balance workload across selected team members
5. Don't select members unless they will receive at least one task

IMPORTANT RULES:
- Form a team of 2-5 members based on task requirements
- Assign ONLY the most critical and urgent tasks (roughly 50-70% of total tasks)
- Leave some tasks unassigned so the project manager can manually assign them later
- Higher priority tasks should be assigned first
- Tasks with earlier deadlines should be prioritized
- Only include team members who will actually receive tasks
- Focus on high and medium priority tasks, leave most low priority tasks unassigned

Return a JSON object in this exact format:
{{
    "team": [
        {{
            "member_id": "member_id_here",
            "member_name": "name",
            "role": "role",
            "selection_reasoning": "Why this member was selected for the team"
        }}
    ],
    "assignments": [
        {{
            "task_id": "task_id_here",
            "member_id": "member_id_here",
            "reasoning": "Brief explanation of why this assignment makes sense"
        }}
    ]
}}

IMPORTANT: Return ONLY the JSON object, no additional text. Out of {len(task_data)} tasks, assign roughly 50-70% of them, prioritizing high-priority and urgent tasks. Leave the rest unassigned for manual assignment."""

        # Use Claude or Gemini to make intelligent assignments
        if USE_CLAUDE and anthropic_client:
            try:
                message = anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                response_text = message.content[0].text.strip()
                ai_provider = "Claude AI"
            except Exception as claude_error:
                print(f"Claude API failed: {claude_error}")
                if USE_GEMINI:
                    model = genai.GenerativeModel("gemini-2.0-flash-exp")
                    response = model.generate_content(contents=prompt)
                    response_text = response.text.strip()
                    ai_provider = "Gemini AI (fallback)"
                else:
                    raise
        elif USE_GEMINI:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            response = model.generate_content(contents=prompt)
            response_text = response.text.strip()
            ai_provider = "Gemini AI"
        else:
            return {"error": "No AI API available for task assignment"}

        # Parse response
        response_text = (
            response_text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

        result = json.loads(response_text)
        team = result.get("team", [])
        assignments = result.get("assignments", [])

        # First, add selected team members to the project
        project = Project.query.get(project_id)
        team_members_added = []

        for team_member_info in team:
            member_id = team_member_info.get("member_id")
            member = TeamMember.query.get(member_id)

            if member:
                # Check if already in project
                existing = ProjectMember.query.filter_by(
                    project_id=project_id, member_id=member_id
                ).first()

                if not existing:
                    project_member = ProjectMember(
                        project_id=project_id, member_id=member_id
                    )
                    db.session.add(project_member)
                    team_members_added.append(
                        {
                            "member_id": member_id,
                            "member_name": member.name,
                            "member_role": member.role,
                            "reasoning": team_member_info.get(
                                "selection_reasoning", ""
                            ),
                        }
                    )

        # Apply task assignments to database
        assignments_made = []
        for assignment in assignments:
            task_id = assignment.get("task_id")
            member_id = assignment.get("member_id")
            reasoning = assignment.get("reasoning", "")

            task = Task.query.get(task_id)
            member = TeamMember.query.get(member_id)

            if task and member:
                task.assigned_to = member_id
                task.updated_at = datetime.utcnow()
                assignments_made.append(
                    {
                        "task_id": task_id,
                        "task_title": task.title,
                        "task_priority": task.priority,
                        "member_id": member_id,
                        "member_name": member.name,
                        "member_role": member.role,
                        "reasoning": reasoning,
                    }
                )

        db.session.commit()

        # Trigger mindmap sync after assignments
        sync_mindmap_internal()

        return {
            "success": True,
            "assigned_by": ai_provider,
            "team_formed": len(team_members_added),
            "team_members": team_members_added,
            "assignments_made": len(assignments_made),
            "assignments": assignments_made,
            "total_tasks": len(task_data),
        }

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return {"error": f"Failed to parse AI response: {str(e)}"}
    except Exception as e:
        print(f"Task assignment error: {e}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


def generate_task_breakdown_with_claude(project_name: str, pdf_content: str) -> dict:
    """
    Use Claude AI to generate short detailed task breakdown and timeline from PDF content
    Falls back to Gemini if Claude fails
    """
    try:
        prompt = f"""You are a project planning expert. Analyze the following project document and create a comprehensive, short detailed action plan.

PROJECT NAME: {project_name}

DOCUMENT CONTENT:
{pdf_content}

Please provide a short detailed analysis in JSON format with the following structure:

{{
    "project_overview": {{
        "objectives": ["list of main objectives"],
        "target_audience": "description of target users",
        "business_value": "description of business value"
    }},
    "key_features": [
        {{
            "feature": "feature name",
            "description": "short description",
            "priority": "high/medium/low"
        }}
    ],
    "technical_requirements": {{
        "tech_stack": ["list of technologies needed"],
        "apis_integrations": ["list of required APIs and integrations"],
        "data_models": ["key database models/schemas"],
        "security": ["security considerations"]
    }},
    "implementation_phases": [
        {{
            "phase": "Phase name",
            "description": "Phase description",
            "tasks": ["list of tasks in this phase"],
            "estimated_days": 0
        }}
    ],
    "subtasks": [
        {{
            "id": "task-1",
            "title": "Task title",
            "description": "short task description",
            "priority": "high/medium/low",
            "estimated_hours": 0,
            "required_role": "Backend Developer/Frontend Developer/Designer/DevOps/QA/Full Stack Developer",
            "dependencies": ["list of task IDs this depends on"],
            "deliverables": ["what will be delivered"]
        }}
    ],
    "challenges": [
        {{
            "challenge": "Challenge description",
            "mitigation": "How to address it",
            "risk_level": "high/medium/low"
        }}
    ],
    "timeline": {{
        "total_estimated_hours": 0,
        "total_estimated_days": 0,
        "recommended_team_size": 0
    }},
    "success_criteria": [
        "Measurable success criterion"
    ]
}}

Be specific, and practical. Base your analysis entirely on the document content provided. Include the "required_role" field for each subtask to help with smart task assignment.

IMPORTANT: Return ONLY the JSON object, no additional text or markdown formatting."""

        # Try Claude first
        if USE_CLAUDE and anthropic_client:
            try:
                print("DEBUG: Attempting to use Claude API...")
                message = anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                )
                response_text = message.content[0].text.strip()
                ai_provider = "Claude AI"
                print("DEBUG: Claude API successful!")
            except Exception as claude_error:
                print(f"DEBUG: Claude API failed: {claude_error}")
                raise  # Re-raise to trigger fallback
        else:
            raise Exception("Claude not available")

    except Exception as e:
        # Fallback to Gemini if Claude fails
        print(f"Claude error: {e}. Falling back to Gemini...")
        if USE_GEMINI:
            try:
                print("DEBUG: Using Gemini API as fallback...")
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(contents=prompt)
                response_text = response.text.strip()
                ai_provider = "Gemini AI (fallback)"
                print("DEBUG: Gemini API successful!")
            except Exception as gemini_error:
                print(f"Gemini API also failed: {gemini_error}")
                return {
                    "error": f"Both Claude and Gemini failed. Claude: {str(e)}, Gemini: {str(gemini_error)}",
                    "subtasks": [],
                    "total_subtasks": 0,
                }
        else:
            return {
                "error": f"Claude failed and Gemini not available: {str(e)}",
                "subtasks": [],
                "total_subtasks": 0,
            }

    try:
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        task_data = json.loads(response_text)

        # Ensure subtasks key exists and calculate total
        if "subtasks" not in task_data:
            task_data["subtasks"] = []

        task_data["total_subtasks"] = len(task_data["subtasks"])
        task_data["original_task"] = project_name
        task_data["generated_by"] = ai_provider

        return task_data

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(
            f"Response text: {response_text if 'response_text' in locals() else 'No response'}"
        )
        return {
            "error": "Failed to parse AI response",
            "subtasks": [],
            "total_subtasks": 0,
        }
    except Exception as e:
        print(f"AI API error: {e}")
        return {
            "error": str(e),
            "subtasks": [],
            "total_subtasks": 0,
        }


def analyze_document_with_mcp(filepath):
    """Analyze document using Claude MCP instead of direct PDF extraction"""
    try:
        # Extract basic file metadata
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)

        # Try to extract PDF text for MCP to analyze
        try:
            import PyPDF2

            with open(filepath, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                num_pages = len(pdf_reader.pages)

                # Extract text from all pages
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text() + "\n\n"

                # Return structured data with actual content for MCP to analyze
                result = {
                    "filename": filename,
                    "filepath": filepath,
                    "file_size": file_size,
                    "num_pages": num_pages,
                    "file_type": "PDF Document",
                    "content": text_content.strip()[:5000],  # First 5000 chars
                    "full_content": text_content.strip(),  # Full content for MCP
                    "analysis_method": "Claude MCP",
                    "status": "ready_for_analysis",
                }
                return json.dumps(result, indent=2)

        except ImportError:
            # Fallback if PyPDF2 not available
            result = {
                "filename": filename,
                "filepath": filepath,
                "file_size": file_size,
                "file_type": "PDF Document",
                "analysis_method": "Claude MCP",
                "message": "PDF text extraction requires PyPDF2. Install with: pip install PyPDF2",
                "status": "metadata_only",
            }
            return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps(
            {"error": f"Error analyzing document: {str(e)}", "status": "error"}
        )


def generate_code_summary(project, analysis_results):
    """Generate a summary of code working and changes"""
    summary = f"# Code Summary for {project.project_name}\n\n"

    # Git status summary
    git_status = analysis_results.get("gitStatus", {})
    if "branch" in git_status:
        summary += f"## Current Repository Status\n"
        summary += f"- Branch: {git_status.get('branch', 'unknown')}\n"
        summary += f"- Changed files: {git_status.get('total_changes', 0)}\n\n"

        if git_status.get("files"):
            summary += "### Modified Files:\n"
            for file_info in git_status.get("files", [])[:10]:
                summary += (
                    f"- {file_info.get('status', '??')} {file_info.get('file', '')}\n"
                )
            summary += "\n"

    # Project statistics
    proj_stats = analysis_results.get("projectStats", {})
    if "total_files" in proj_stats:
        summary += f"## Project Statistics\n"
        summary += f"- Total files: {proj_stats.get('total_files', 0)}\n"
        summary += f"- Total lines: {proj_stats.get('total_lines', 0)}\n"
        summary += (
            f"- Programming languages: {', '.join(proj_stats.get('languages', []))}\n\n"
        )

    # Task breakdown
    task_breakdown = analysis_results.get("taskBreakdown", {})
    if "subtasks" in task_breakdown:
        summary += f"## Task Breakdown\n"
        summary += f"Total subtasks: {task_breakdown.get('total_subtasks', 0)}\n\n"
        for task in task_breakdown.get("subtasks", [])[:5]:
            summary += f"### {task.get('title', 'Untitled')}\n"
            summary += f"- Priority: {task.get('priority', 'medium')}\n"
            summary += f"- Estimated hours: {task.get('estimated_hours', 0)}\n\n"

    # Time estimate
    time_est = analysis_results.get("timeEstimate", {})
    if "estimated_hours" in time_est:
        summary += f"## Time Estimate\n"
        summary += f"- Estimated hours: {time_est.get('estimated_hours', 0)}\n"
        summary += f"- Estimated days: {time_est.get('estimated_days', 0)}\n"
        summary += f"- Complexity: {time_est.get('complexity', 'medium')}\n"
        summary += f"- Confidence: {time_est.get('confidence', 'medium')}\n\n"

    summary += f"## Changes Summary\n"
    summary += "This analysis was performed using Claude MCP integration to provide:\n"
    summary += "1. Detailed task breakdown from project requirements\n"
    summary += "2. Time estimates for implementation\n"
    summary += "3. Current git repository status\n"
    summary += "4. Project code statistics and structure\n"

    return summary


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
