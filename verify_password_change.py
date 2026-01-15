
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_change_password():
    print("--- Testing Password Change ---")

    # 1. Register a temp user
    username = "testuser_pw_change"
    password = "InitialPassword123!"
    email = "testpw@example.com"
    
    print(f"Registering user {username}...")
    resp = requests.post(f"{BASE_URL}/register/", json={
        "username": username,
        "password": password,
        "email": email
    })
    
    if resp.status_code == 201:
        token = resp.json()['token']
        print("Registration successful.")
    elif resp.status_code == 400 and 'username' in resp.json():
        # User might exist, try login
        print("User exists, logging in...")
        l_resp = requests.post(f"{BASE_URL}/api-token-auth/", json={
            "username": username,
            "password": password
        })
        if l_resp.status_code == 200:
            token = l_resp.json()['token']
        else:
            # Maybe password was already changed in previous run? Try new password
            l_resp2 = requests.post(f"{BASE_URL}/api-token-auth/", json={
                "username": username,
                "password": "NewPassword456!"
            })
            if l_resp2.status_code == 200:
                 token = l_resp2.json()['token']
                 password = "NewPassword456!" # Current password is now the new one
            else:
                print("Could not login. Manual cleanup needed.")
                sys.exit(1)
    else:
        print(f"Registration failed: {resp.text}")
        sys.exit(1)

    headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}

    # 2. Try Changing Password with WRONG old password
    print("Attempting with WRONG old password...")
    resp = requests.post(f"{BASE_URL}/change-password/", headers=headers, json={
        "old_password": "WrongPassword",
        "new_password": "NewPassword456!"
    })
    if resp.status_code == 400:
        print("PASS: Correctly rejected wrong old password.")
    else:
        print(f"FAIL: Expected 400, got {resp.status_code}")

    # 3. Success Case
    new_password = "NewPassword456!"
    if password == new_password: new_password = "InitialPassword123!" # Toggle back if needed

    print(f"Attempting to change password to {new_password}...")
    resp = requests.post(f"{BASE_URL}/change-password/", headers=headers, json={
        "old_password": password,
        "new_password": new_password
    })
    
    if resp.status_code == 200:
        print("PASS: Password change request successful.")
    else:
        print(f"FAIL: {resp.text}")
        sys.exit(1)

    # 4. Verify Login with OLD password (should fail)
    print("Verifying OLD password login fails...")
    resp = requests.post(f"{BASE_URL}/api-token-auth/", json={
        "username": username,
        "password": password
    })
    if resp.status_code != 200:
        print("PASS: Old password rejected.")
    else:
        print("FAIL: Old password still works!")

    # 5. Verify Login with NEW password (should success)
    print("Verifying NEW password login succeeds...")
    resp = requests.post(f"{BASE_URL}/api-token-auth/", json={
        "username": username,
        "password": new_password
    })
    if resp.status_code == 200:
        print("PASS: New password accepted.")
    else:
        print(f"FAIL: New password rejected! {resp.text}")

if __name__ == "__main__":
    test_change_password()
