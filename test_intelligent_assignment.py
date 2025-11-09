"""
Test script for intelligent task assignment with Claude MCP
Run this after starting the Flask app to test the auto-assignment feature
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_auto_assignment():
    """Test the intelligent task assignment endpoint"""
    print("🧪 Testing Intelligent Task Assignment with Claude MCP\n")
    print("=" * 60)

    # Step 1: Get existing projects
    print("\n1️⃣ Fetching projects...")
    response = requests.get(f"{BASE_URL}/api/projects")
    if response.status_code != 200:
        print("❌ Failed to fetch projects")
        return

    projects = response.json()
    if not projects:
        print("⚠️  No projects found. Please create a project first.")
        return

    project_id = projects[0]["id"]
    project_name = projects[0]["name"]
    print(f"✅ Found project: {project_name} (ID: {project_id})")

    # Step 2: Get team members
    print("\n2️⃣ Fetching team members...")
    response = requests.get(f"{BASE_URL}/api/team-members")
    if response.status_code != 200:
        print("❌ Failed to fetch team members")
        return

    members = response.json()
    print(f"✅ Found {len(members)} team members:")
    for member in members:
        print(f"   • {member['name']} - {member['role']}")

    # Step 3: Check for unassigned tasks
    print("\n3️⃣ Checking unassigned tasks...")
    response = requests.get(f"{BASE_URL}/api/tasks")
    if response.status_code != 200:
        print("❌ Failed to fetch tasks")
        return

    all_tasks = response.json()
    unassigned_tasks = [t for t in all_tasks if not t.get("assignedTo")]
    print(f"✅ Found {len(unassigned_tasks)} unassigned tasks")

    if not unassigned_tasks:
        print("⚠️  No unassigned tasks. Creating some test tasks...")
        # Create test tasks
        test_tasks = [
            {
                "title": "Design user authentication UI",
                "priority": "high",
                "deadline": "Dec 15",
                "projectId": project_id,
            },
            {
                "title": "Implement REST API endpoints",
                "priority": "high",
                "deadline": "Dec 20",
                "projectId": project_id,
            },
            {
                "title": "Write integration tests",
                "priority": "medium",
                "deadline": "Dec 25",
                "projectId": project_id,
            },
            {
                "title": "Setup database migrations",
                "priority": "medium",
                "deadline": "Dec 18",
                "projectId": project_id,
            },
        ]

        for task in test_tasks:
            response = requests.post(f"{BASE_URL}/api/tasks", json=task)
            if response.status_code == 200:
                print(f"   ✅ Created: {task['title']}")

    # Step 4: Trigger intelligent auto-assignment
    print("\n4️⃣ Triggering intelligent auto-assignment...")
    print("   🤖 Claude AI is analyzing tasks and team members...")
    print("   ⏳ This may take a few seconds...\n")

    response = requests.post(f"{BASE_URL}/api/projects/{project_id}/auto-assign")

    if response.status_code != 200:
        print(f"❌ Auto-assignment failed: {response.json()}")
        return

    result = response.json()

    # Step 5: Display results
    print("\n" + "=" * 60)
    print("🎉 AUTO-ASSIGNMENT COMPLETED!")
    print("=" * 60)

    print(f"\n📊 Summary:")
    print(f"   • AI Provider: {result.get('assigned_by', 'Unknown')}")
    print(f"   • Assignments Made: {result.get('assignments_made', 0)}")

    if result.get("assignments"):
        print(f"\n📋 Assignment Details:\n")
        for idx, assignment in enumerate(result["assignments"], 1):
            print(f"{idx}. Task: {assignment['task_title']}")
            print(f"   Assigned to: {assignment['member_name']} ({assignment['member_role']})")
            print(f"   Reasoning: {assignment['reasoning']}")
            print()

    # Step 6: Verify assignments in database
    print("\n5️⃣ Verifying assignments...")
    response = requests.get(f"{BASE_URL}/api/tasks")
    if response.status_code == 200:
        tasks = response.json()
        assigned_count = len([t for t in tasks if t.get("assignedTo")])
        print(f"✅ {assigned_count} tasks are now assigned")

    print("\n" + "=" * 60)
    print("✨ Test completed! Check the dashboard to see the assignments.")
    print("=" * 60)


def test_workload_distribution():
    """Analyze workload distribution after assignment"""
    print("\n\n📊 WORKLOAD DISTRIBUTION ANALYSIS")
    print("=" * 60)

    # Get all team members
    response = requests.get(f"{BASE_URL}/api/team-members")
    if response.status_code != 200:
        print("❌ Failed to fetch team members")
        return

    members = response.json()

    # Get all tasks
    response = requests.get(f"{BASE_URL}/api/tasks")
    if response.status_code != 200:
        print("❌ Failed to fetch tasks")
        return

    tasks = response.json()

    # Calculate workload per member
    print("\nWorkload per team member:\n")
    for member in members:
        member_tasks = [t for t in tasks if t.get("assignedTo") == member["id"]]
        task_count = len(member_tasks)
        print(f"👤 {member['name']} ({member['role']})")
        print(f"   Tasks: {task_count}")
        if task_count > 0:
            print("   Tasks:")
            for task in member_tasks:
                print(f"      • {task['title']} [{task['priority']}]")
        print()


if __name__ == "__main__":
    print("\n" + "🤖 CLAUDE MCP INTELLIGENT TASK ASSIGNMENT TEST" + "\n")
    print("Prerequisites:")
    print("1. Flask app is running on http://localhost:8000")
    print("2. ANTHROPIC_API_KEY is set in environment")
    print("3. At least one project exists")
    print("4. Team members are added\n")

    input("Press Enter to continue...")

    try:
        test_auto_assignment()
        test_workload_distribution()
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to Flask app. Make sure it's running!")
        print("   Run: python app.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
