import os
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "project_tracker.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

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

    task.assigned_to = data.get("assignedTo")
    task.updated_at = datetime.utcnow()
    db.session.commit()

    # Trigger mindmap sync after assignment change
    sync_mindmap_internal()

    return jsonify(task.to_dict())


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
        ]

        for member in default_members:
            db.session.add(member)

    if Project.query.count() == 0:
        default_projects = [
            Project(
                id="vocalift",
                name="VocaLift (i18n Tool)",
                tag_color="yellow",
                description="Internationalization platform for seamless multi-language support across applications.",
            ),
            Project(
                id="authn-mfa",
                name="AuthN-MFA-Rollout",
                tag_color="green",
                description="Multi-factor authentication system rollout for enhanced security protocols.",
            ),
            Project(
                id="billing-v2",
                name="Billing-Orchestrator-v2",
                tag_color="blue",
                description="Next-generation billing infrastructure with improved scalability and performance.",
            ),
        ]

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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
