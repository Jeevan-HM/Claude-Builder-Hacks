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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # For future PDF integration
    pdf_content = db.Column(db.Text, nullable=True)
    pdf_metadata = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "text": self.text,
            "level": self.level,
            "pdf_content": self.pdf_content,
            "pdf_metadata": self.pdf_metadata,
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


class Settings(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(500), nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {"key": self.key, "value": self.value}


# ==================== ROUTES ====================


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/team")
def team_dashboard():
    return render_template("team_dashboard.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


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
        # Update existing node
        node = Node.query.get(data["id"])
        if node:
            node.x = data.get("x", node.x)
            node.y = data.get("y", node.y)
            node.text = data.get("text", node.text)
            node.level = data.get("level", node.level)
            node.pdf_content = data.get("pdf_content", node.pdf_content)
            node.pdf_metadata = data.get("pdf_metadata", node.pdf_metadata)
            node.updated_at = datetime.utcnow()
        else:
            return jsonify({"error": "Node not found"}), 404
    else:
        # Create new node
        node = Node(
            x=data["x"],
            y=data["y"],
            text=data["text"],
            level=data.get("level", 0),
            pdf_content=data.get("pdf_content"),
            pdf_metadata=data.get("pdf_metadata"),
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

    # Delete associated connections
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

    # Check if connection already exists
    existing = Connection.query.filter_by(
        from_node=data["from"], to_node=data["to"]
    ).first()

    if existing:
        return jsonify(existing.to_dict())

    connection = Connection(from_node=data["from"], to_node=data["to"])
    db.session.add(connection)
    db.session.commit()
    return jsonify(connection.to_dict())


# Delete a connection
@app.route("/api/connections/<int:conn_id>", methods=["DELETE"])
def delete_connection(conn_id):
    connection = Connection.query.get(conn_id)
    if not connection:
        return jsonify({"error": "Connection not found"}), 404

    db.session.delete(connection)
    db.session.commit()
    return jsonify({"success": True})


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


# Get/Set settings
@app.route("/api/settings/<key>", methods=["GET"])
def get_setting(key):
    setting = Settings.query.get(key)
    if not setting:
        return jsonify({"value": None})
    return jsonify(setting.to_dict())


@app.route("/api/settings", methods=["POST"])
def set_setting():
    data = request.json
    setting = Settings.query.get(data["key"])

    if setting:
        setting.value = data["value"]
        setting.updated_at = datetime.utcnow()
    else:
        setting = Settings(key=data["key"], value=data["value"])
        db.session.add(setting)

    db.session.commit()
    return jsonify(setting.to_dict())


# Clear all data
@app.route("/api/clear-all", methods=["DELETE"])
def clear_all():
    try:
        Connection.query.delete()
        Node.query.delete()
        Settings.query.delete()
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Initialize database
@app.route("/api/init-db", methods=["POST"])
def init_db():
    db.create_all()

    #     # Check if we need to add default data
    if Node.query.count() == 0:
        default_nodes = [
            Node(id=0, x=150, y=250, text="Project: Ares IV Colony", level=0),
            Node(id=1, x=550, y=180, text="PM: Dr. Eva Rostova", level=1),
            Node(id=2, x=950, y=100, text="Senior Developers", level=2),
            Node(id=3, x=950, y=260, text="Junior Developers", level=2),
            Node(id=4, x=1400, y=50, text="Mika Petrova", level=3),
            Node(id=5, x=1400, y=120, text="Dr. Aris Thorne", level=3),
            Node(id=6, x=1400, y=220, text="Leo Kwan", level=3),
            Node(id=7, x=1400, y=280, text="Ria Sharma", level=3),
            Node(id=8, x=1400, y=340, text="Zane Al-Jamil", level=3),
            Node(id=9, x=150, y=600, text="Project: Neptune Deep-Dive", level=0),
            Node(id=10, x=550, y=600, text="PM: Jax Riley", level=1),
            Node(id=11, x=950, y=540, text="Senior Developers", level=2),
            Node(id=12, x=950, y=660, text="Junior Developers", level=2),
            Node(id=13, x=1400, y=540, text="Kenji Tanaka", level=3),
            Node(id=14, x=1400, y=640, text="Sora Kim", level=3),
            Node(id=15, x=1400, y=700, text="Finn O'Malley", level=3),
        ]

        default_connections = [
            Connection(from_node=0, to_node=1),
            Connection(from_node=1, to_node=2),
            Connection(from_node=1, to_node=3),
            Connection(from_node=2, to_node=4),
            Connection(from_node=2, to_node=5),
            Connection(from_node=3, to_node=6),
            Connection(from_node=3, to_node=7),
            Connection(from_node=3, to_node=8),
            Connection(from_node=9, to_node=10),
            Connection(from_node=10, to_node=11),
            Connection(from_node=10, to_node=12),
            Connection(from_node=11, to_node=13),
            Connection(from_node=12, to_node=14),
            Connection(from_node=12, to_node=15),
        ]

        # default_nodes = []
        # default_connections = []

        for node in default_nodes:
            db.session.add(node)
        for conn in default_connections:
            db.session.add(conn)

        db.session.commit()

    return jsonify({"success": True, "message": "Database initialized"})


# Database health check
@app.route("/api/health", methods=["GET"])
def health_check():
    try:
        node_count = Node.query.count()
        conn_count = Connection.query.count()
        return jsonify(
            {"status": "healthy", "nodes": node_count, "connections": conn_count}
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
