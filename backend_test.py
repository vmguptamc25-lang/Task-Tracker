#!/usr/bin/env python3
"""
Comprehensive backend API tests for Task Tracker
Tests all auth endpoints and task CRUD operations
"""
import requests
import json
import time
from datetime import datetime

# Base URL from .env
BASE_URL = "https://task-manager-pro-76.preview.emergentagent.com/api"

def print_test(name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"   Details: {details}")

def generate_unique_email():
    """Generate unique email to avoid conflicts"""
    timestamp = int(time.time() * 1000)
    return f"testuser{timestamp}@example.com"

def test_health():
    """Test GET /api/health"""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        data = response.json()
        passed = response.status_code == 200 and data.get("status") == "ok"
        print_test("GET /api/health", passed, f"Status: {response.status_code}, Response: {data}")
        return passed
    except Exception as e:
        print_test("GET /api/health", False, f"Exception: {str(e)}")
        return False

def test_signup_validation():
    """Test signup validation rules"""
    print("\n=== Testing Signup Validation ===")
    all_passed = True
    
    # Test missing fields
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", 
                                json={"email": "test@test.com"}, 
                                timeout=10)
        passed = response.status_code == 400
        print_test("Signup missing fields returns 400", passed, 
                  f"Status: {response.status_code}")
        all_passed = all_passed and passed
    except Exception as e:
        print_test("Signup missing fields returns 400", False, f"Exception: {str(e)}")
        all_passed = False
    
    # Test short password
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", 
                                json={"email": "test@test.com", "password": "12345", "name": "Test"}, 
                                timeout=10)
        passed = response.status_code == 400
        print_test("Signup with password <6 chars returns 400", passed, 
                  f"Status: {response.status_code}")
        all_passed = all_passed and passed
    except Exception as e:
        print_test("Signup with password <6 chars returns 400", False, f"Exception: {str(e)}")
        all_passed = False
    
    return all_passed

def test_signup_and_login():
    """Test signup and login flow"""
    print("\n=== Testing Signup and Login Flow ===")
    
    email = generate_unique_email()
    password = "testpass123"
    name = "Test User"
    
    # Test signup
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", 
                                json={"email": email, "password": password, "name": name}, 
                                timeout=10)
        data = response.json()
        
        signup_passed = (
            response.status_code == 200 and 
            "token" in data and 
            "user" in data and
            data["user"]["email"] == email.lower() and
            data["user"]["name"] == name and
            "password" not in data["user"]
        )
        print_test("Signup creates user and returns token", signup_passed, 
                  f"Status: {response.status_code}, Has token: {'token' in data}, Has user: {'user' in data}")
        
        if not signup_passed:
            return False, None, None
        
        token = data["token"]
        user_id = data["user"]["id"]
        
    except Exception as e:
        print_test("Signup creates user and returns token", False, f"Exception: {str(e)}")
        return False, None, None
    
    # Test duplicate signup
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", 
                                json={"email": email, "password": password, "name": name}, 
                                timeout=10)
        passed = response.status_code == 409
        print_test("Duplicate email returns 409", passed, f"Status: {response.status_code}")
    except Exception as e:
        print_test("Duplicate email returns 409", False, f"Exception: {str(e)}")
    
    # Test login with correct credentials
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                                json={"email": email, "password": password}, 
                                timeout=10)
        data = response.json()
        
        login_passed = (
            response.status_code == 200 and 
            "token" in data and 
            "user" in data and
            "password" not in data["user"]
        )
        print_test("Login with correct credentials returns token", login_passed, 
                  f"Status: {response.status_code}")
        
        if not login_passed:
            return False, None, None
            
    except Exception as e:
        print_test("Login with correct credentials returns token", False, f"Exception: {str(e)}")
        return False, None, None
    
    # Test login with wrong password
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                                json={"email": email, "password": "wrongpass"}, 
                                timeout=10)
        passed = response.status_code == 401
        print_test("Login with wrong password returns 401", passed, f"Status: {response.status_code}")
    except Exception as e:
        print_test("Login with wrong password returns 401", False, f"Exception: {str(e)}")
    
    # Test login with non-existent user
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                                json={"email": "nonexistent@test.com", "password": password}, 
                                timeout=10)
        passed = response.status_code == 401
        print_test("Login with non-existent user returns 401", passed, f"Status: {response.status_code}")
    except Exception as e:
        print_test("Login with non-existent user returns 401", False, f"Exception: {str(e)}")
    
    return True, token, user_id

def test_auth_me(token):
    """Test GET /api/auth/me"""
    print("\n=== Testing Auth Me Endpoint ===")
    
    # Test without token
    try:
        response = requests.get(f"{BASE_URL}/auth/me", timeout=10)
        passed = response.status_code == 401
        print_test("GET /api/auth/me without token returns 401", passed, 
                  f"Status: {response.status_code}")
    except Exception as e:
        print_test("GET /api/auth/me without token returns 401", False, f"Exception: {str(e)}")
    
    # Test with valid token
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and 
            "user" in data and
            "password" not in data["user"]
        )
        print_test("GET /api/auth/me with token returns user", passed, 
                  f"Status: {response.status_code}, Has user: {'user' in data}, No password: {'password' not in data.get('user', {})}")
        return passed
    except Exception as e:
        print_test("GET /api/auth/me with token returns user", False, f"Exception: {str(e)}")
        return False

def test_tasks_crud(token):
    """Test tasks CRUD operations"""
    print("\n=== Testing Tasks CRUD ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test unauthorized access
    try:
        response = requests.get(f"{BASE_URL}/tasks", timeout=10)
        passed = response.status_code == 401
        print_test("GET /api/tasks without token returns 401", passed, 
                  f"Status: {response.status_code}")
    except Exception as e:
        print_test("GET /api/tasks without token returns 401", False, f"Exception: {str(e)}")
    
    # Test POST task
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "priority": "high",
        "dueDate": "2024-12-31"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks", 
                                json=task_data, 
                                headers=headers, 
                                timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and 
            "task" in data and
            data["task"]["title"] == task_data["title"] and
            data["task"]["description"] == task_data["description"] and
            data["task"]["priority"] == task_data["priority"] and
            "id" in data["task"]
        )
        print_test("POST /api/tasks creates task", passed, 
                  f"Status: {response.status_code}, Has task: {'task' in data}")
        
        if not passed:
            return False
        
        task_id = data["task"]["id"]
        
    except Exception as e:
        print_test("POST /api/tasks creates task", False, f"Exception: {str(e)}")
        return False
    
    # Test GET tasks
    try:
        response = requests.get(f"{BASE_URL}/tasks", headers=headers, timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and 
            "tasks" in data and
            isinstance(data["tasks"], list) and
            len(data["tasks"]) > 0
        )
        print_test("GET /api/tasks returns user's tasks", passed, 
                  f"Status: {response.status_code}, Task count: {len(data.get('tasks', []))}")
    except Exception as e:
        print_test("GET /api/tasks returns user's tasks", False, f"Exception: {str(e)}")
    
    # Test PUT task
    update_data = {
        "title": "Updated Task",
        "description": "Updated description",
        "priority": "low",
        "status": "in-progress"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", 
                               json=update_data, 
                               headers=headers, 
                               timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and 
            "task" in data and
            data["task"]["title"] == update_data["title"] and
            data["task"]["description"] == update_data["description"] and
            data["task"]["priority"] == update_data["priority"]
        )
        print_test("PUT /api/tasks/:id updates task", passed, 
                  f"Status: {response.status_code}")
    except Exception as e:
        print_test("PUT /api/tasks/:id updates task", False, f"Exception: {str(e)}")
    
    # Test completed/status sync
    try:
        response = requests.put(f"{BASE_URL}/tasks/{task_id}", 
                               json={"completed": True}, 
                               headers=headers, 
                               timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and 
            data["task"]["completed"] == True and
            data["task"]["status"] == "done"
        )
        print_test("Setting completed=true syncs status to 'done'", passed, 
                  f"Status: {response.status_code}, completed: {data.get('task', {}).get('completed')}, status: {data.get('task', {}).get('status')}")
    except Exception as e:
        print_test("Setting completed=true syncs status to 'done'", False, f"Exception: {str(e)}")
    
    # Test DELETE task
    try:
        response = requests.delete(f"{BASE_URL}/tasks/{task_id}", 
                                  headers=headers, 
                                  timeout=10)
        data = response.json()
        
        passed = (
            response.status_code == 200 and 
            data.get("success") == True
        )
        print_test("DELETE /api/tasks/:id deletes task", passed, 
                  f"Status: {response.status_code}, Success: {data.get('success')}")
    except Exception as e:
        print_test("DELETE /api/tasks/:id deletes task", False, f"Exception: {str(e)}")
    
    # Test DELETE non-existent task
    try:
        response = requests.delete(f"{BASE_URL}/tasks/{task_id}", 
                                  headers=headers, 
                                  timeout=10)
        passed = response.status_code == 404
        print_test("DELETE non-existent task returns 404", passed, 
                  f"Status: {response.status_code}")
    except Exception as e:
        print_test("DELETE non-existent task returns 404", False, f"Exception: {str(e)}")
    
    return True

def test_multi_user_isolation():
    """Test that users can only access their own tasks"""
    print("\n=== Testing Multi-User Isolation ===")
    
    # Create User A
    email_a = generate_unique_email()
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", 
                                json={"email": email_a, "password": "password123", "name": "User A"}, 
                                timeout=10)
        data = response.json()
        if response.status_code != 200:
            print_test("Create User A", False, f"Status: {response.status_code}")
            return False
        token_a = data["token"]
        print_test("Create User A", True, "User A created successfully")
    except Exception as e:
        print_test("Create User A", False, f"Exception: {str(e)}")
        return False
    
    # Create User B
    email_b = generate_unique_email()
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", 
                                json={"email": email_b, "password": "password123", "name": "User B"}, 
                                timeout=10)
        data = response.json()
        if response.status_code != 200:
            print_test("Create User B", False, f"Status: {response.status_code}")
            return False
        token_b = data["token"]
        print_test("Create User B", True, "User B created successfully")
    except Exception as e:
        print_test("Create User B", False, f"Exception: {str(e)}")
        return False
    
    # User A creates a task
    headers_a = {"Authorization": f"Bearer {token_a}"}
    try:
        response = requests.post(f"{BASE_URL}/tasks", 
                                json={"title": "User A's Task", "description": "Private to User A"}, 
                                headers=headers_a, 
                                timeout=10)
        data = response.json()
        if response.status_code != 200:
            print_test("User A creates task", False, f"Status: {response.status_code}")
            return False
        task_a_id = data["task"]["id"]
        print_test("User A creates task", True, f"Task ID: {task_a_id}")
    except Exception as e:
        print_test("User A creates task", False, f"Exception: {str(e)}")
        return False
    
    # User B creates a task
    headers_b = {"Authorization": f"Bearer {token_b}"}
    try:
        response = requests.post(f"{BASE_URL}/tasks", 
                                json={"title": "User B's Task", "description": "Private to User B"}, 
                                headers=headers_b, 
                                timeout=10)
        data = response.json()
        if response.status_code != 200:
            print_test("User B creates task", False, f"Status: {response.status_code}")
            return False
        task_b_id = data["task"]["id"]
        print_test("User B creates task", True, f"Task ID: {task_b_id}")
    except Exception as e:
        print_test("User B creates task", False, f"Exception: {str(e)}")
        return False
    
    # User B tries to view tasks - should only see their own
    try:
        response = requests.get(f"{BASE_URL}/tasks", headers=headers_b, timeout=10)
        data = response.json()
        
        user_b_tasks = data.get("tasks", [])
        has_only_own_tasks = all(task["title"] == "User B's Task" for task in user_b_tasks)
        has_user_a_task = any(task["id"] == task_a_id for task in user_b_tasks)
        
        passed = (
            response.status_code == 200 and 
            len(user_b_tasks) == 1 and
            has_only_own_tasks and
            not has_user_a_task
        )
        print_test("User B cannot see User A's tasks", passed, 
                  f"User B sees {len(user_b_tasks)} task(s), Has User A's task: {has_user_a_task}")
    except Exception as e:
        print_test("User B cannot see User A's tasks", False, f"Exception: {str(e)}")
        return False
    
    # User B tries to update User A's task
    try:
        response = requests.put(f"{BASE_URL}/tasks/{task_a_id}", 
                               json={"title": "Hacked by User B"}, 
                               headers=headers_b, 
                               timeout=10)
        passed = response.status_code == 404
        print_test("User B cannot update User A's task (404)", passed, 
                  f"Status: {response.status_code}")
    except Exception as e:
        print_test("User B cannot update User A's task (404)", False, f"Exception: {str(e)}")
        return False
    
    # User B tries to delete User A's task
    try:
        response = requests.delete(f"{BASE_URL}/tasks/{task_a_id}", 
                                  headers=headers_b, 
                                  timeout=10)
        passed = response.status_code == 404
        print_test("User B cannot delete User A's task (404)", passed, 
                  f"Status: {response.status_code}")
    except Exception as e:
        print_test("User B cannot delete User A's task (404)", False, f"Exception: {str(e)}")
        return False
    
    # Verify User A's task still exists
    try:
        response = requests.get(f"{BASE_URL}/tasks", headers=headers_a, timeout=10)
        data = response.json()
        
        user_a_tasks = data.get("tasks", [])
        task_still_exists = any(task["id"] == task_a_id for task in user_a_tasks)
        
        passed = response.status_code == 200 and task_still_exists
        print_test("User A's task still exists after User B's attempts", passed, 
                  f"Task exists: {task_still_exists}")
        return passed
    except Exception as e:
        print_test("User A's task still exists after User B's attempts", False, f"Exception: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("TASK TRACKER BACKEND API TESTS")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Test started at: {datetime.now().isoformat()}")
    
    results = {
        "health": False,
        "signup_validation": False,
        "signup_login": False,
        "auth_me": False,
        "tasks_crud": False,
        "multi_user_isolation": False
    }
    
    # Run tests
    results["health"] = test_health()
    results["signup_validation"] = test_signup_validation()
    
    signup_success, token, user_id = test_signup_and_login()
    results["signup_login"] = signup_success
    
    if token:
        results["auth_me"] = test_auth_me(token)
        results["tasks_crud"] = test_tasks_crud(token)
    
    results["multi_user_isolation"] = test_multi_user_isolation()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} test suites passed")
    print(f"Test completed at: {datetime.now().isoformat()}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
