#!/usr/bin/env python3
"""
Test authentication endpoints
"""
import requests
import json

BASE_URL = 'http://localhost:5000/api/auth'

def test_signup():
    """Test user registration"""
    print("\n" + "="*60)
    print("TEST 1: User Registration (Signup)")
    print("="*60)
    
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'full_name': 'Test User'
    }
    
    response = requests.post(f'{BASE_URL}/signup', json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("[OK] PASS: User registered successfully")
        return response.json()['token']
    else:
        print("[FAIL] FAIL: Registration failed")
        return None

def test_duplicate_signup():
    """Test duplicate user registration"""
    print("\n" + "="*60)
    print("TEST 2: Duplicate Registration (Should Fail)")
    print("="*60)
    
    data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    }
    
    response = requests.post(f'{BASE_URL}/signup', json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 409:
        print("[OK] PASS: Duplicate registration properly rejected")
    else:
        print("[FAIL] FAIL: Should have rejected duplicate registration")

def test_login():
    """Test user login"""
    print("\n" + "="*60)
    print("TEST 3: User Login")
    print("="*60)
    
    data = {
        'email': 'test@example.com',
        'password': 'password123'
    }
    
    response = requests.post(f'{BASE_URL}/login', json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("[OK] PASS: Login successful")
        return response.json()['token']
    else:
        print("[FAIL] FAIL: Login failed")
        return None

def test_invalid_login():
    """Test login with invalid credentials"""
    print("\n" + "="*60)
    print("TEST 4: Invalid Login (Should Fail)")
    print("="*60)
    
    data = {
        'email': 'test@example.com',
        'password': 'wrongpassword'
    }
    
    response = requests.post(f'{BASE_URL}/login', json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 401:
        print("[OK] PASS: Invalid login properly rejected")
    else:
        print("[FAIL] FAIL: Should have rejected invalid credentials")

def test_verify_token(token):
    """Test token verification"""
    print("\n" + "="*60)
    print("TEST 5: Token Verification")
    print("="*60)
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/verify', headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("[OK] PASS: Token verified successfully")
    else:
        print("[FAIL] FAIL: Token verification failed")

def test_get_current_user(token):
    """Test getting current user profile"""
    print("\n" + "="*60)
    print("TEST 6: Get Current User Profile")
    print("="*60)
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/me', headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("[OK] PASS: Profile retrieved successfully")
    else:
        print("[FAIL] FAIL: Failed to get profile")

def test_protected_route_without_token():
    """Test accessing protected route without token"""
    print("\n" + "="*60)
    print("TEST 7: Protected Route Without Token (Should Fail)")
    print("="*60)
    
    response = requests.get(f'{BASE_URL}/me')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 401:
        print("[OK] PASS: Properly rejected access without token")
    else:
        print("[FAIL] FAIL: Should have rejected access without token")

def test_admin_login():
    """Test admin login"""
    print("\n" + "="*60)
    print("TEST 8: Admin Login")
    print("="*60)
    
    data = {
        'email': 'admin@pakjournal77.com',
        'password': 'admin123'
    }
    
    response = requests.post(f'{BASE_URL}/login', json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200 and response.json()['user']['role'] == 'admin':
        print("[OK] PASS: Admin login successful")
        return response.json()['token']
    else:
        print("[FAIL] FAIL: Admin login failed")
        return None

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PAK JOURNAL ARCHIVE 77 - Authentication Tests")
    print("="*60)
    print("\nMake sure the backend server is running on http://localhost:5000")
    input("Press Enter to start tests...")
    
    try:
        # Test signup
        token = test_signup()
        
        # Test duplicate signup
        test_duplicate_signup()
        
        # Test login
        if not token:
            token = test_login()
        
        # Test invalid login
        test_invalid_login()
        
        # Test protected routes with token
        if token:
            test_verify_token(token)
            test_get_current_user(token)
        
        # Test protected route without token
        test_protected_route_without_token()
        
        # Test admin login
        admin_token = test_admin_login()
        
        print("\n" + "="*60)
        print("[OK] All Tests Completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n[FAIL] ERROR: Cannot connect to backend server")
        print("Make sure the server is running on http://localhost:5000")
    except Exception as e:
        print(f"\n[FAIL] ERROR: {e}")

if __name__ == '__main__':
    main()
