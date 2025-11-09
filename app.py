from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/team-dashboard")
def team_dashboard():
    return render_template("team_dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)
