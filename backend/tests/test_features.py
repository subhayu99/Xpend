import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = f"test_user_{int(datetime.now().timestamp())}@example.com"
PASSWORD = "Password123!"

def print_step(step):
    print(f"\n{'='*50}\n{step}\n{'='*50}")

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def test_flow():
    # 1. Register and Login
    print_step("1. Authentication")
    
    # Register
    reg_data = {"email": EMAIL, "password": PASSWORD, "name": "Test User"}
    resp = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    if resp.status_code == 201:
        print_success("User registered")
    else:
        print_error(f"Registration failed: {resp.text}")
        return

    # Login
    login_data = {"email": EMAIL, "password": PASSWORD}
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print_success("Logged in successfully")
    else:
        print_error(f"Login failed: {resp.text}")
        return

    # 2. Create Accounts
    print_step("2. Account Creation")
    
    # Account 1 (HDFC)
    acc1_data = {"name": "HDFC Savings", "bank_name": "HDFC", "account_type": "savings", "balance": 50000}
    resp = requests.post(f"{BASE_URL}/accounts", json=acc1_data, headers=headers)
    acc1_id = resp.json()["id"]
    print_success(f"Created Account 1: {acc1_id}")
    
    # Account 2 (SBI)
    acc2_data = {"name": "SBI Savings", "bank_name": "SBI", "account_type": "savings", "balance": 20000}
    resp = requests.post(f"{BASE_URL}/accounts", json=acc2_data, headers=headers)
    acc2_id = resp.json()["id"]
    print_success(f"Created Account 2: {acc2_id}")

    # 3. Test Manual Transaction Entry
    print_step("3. Manual Transaction Entry")
    
    # Transaction 1: Expense
    tx1_data = {
        "account_id": acc1_id,
        "amount": -1500,
        "description": "Grocery Shopping",
        "transaction_date": datetime.now().strftime("%Y-%m-%d"),
        "transaction_type": "expense"
    }
    resp = requests.post(f"{BASE_URL}/transactions", json=tx1_data, headers=headers)
    if resp.status_code == 201:
        print_success("Created manual expense transaction")
    else:
        print_error(f"Failed to create transaction: {resp.text}")

    # 4. Test Merchant Normalization
    print_step("4. Merchant Normalization")
    
    # Create transaction with messy description
    messy_tx_data = {
        "account_id": acc1_id,
        "amount": -450,
        "description": "UPI/SWIGGY*DELHI/123456/PAYMENT",
        "transaction_date": datetime.now().strftime("%Y-%m-%d"),
        "transaction_type": "expense"
    }
    # Note: The API endpoint we created for manual entry doesn't call the normalizer automatically 
    # (that happens in the parser service). But let's check if we can update it or if we need to fix that.
    # Actually, let's check the code. The manual entry endpoint just saves what is sent.
    # The normalizer is used in StatementParserService.
    # So for this test, we'll simulate what the frontend would send if it used the normalizer, 
    # OR we can verify the normalizer utility directly in a separate script.
    # Let's skip this check via API for now and verify the utility works in unit test style later.
    print("Skipping API check for normalization (happens during file parse). Will verify utility separately.")

    # 5. Test Advanced Filters
    print_step("5. Advanced Filters")
    
    # Create a few more transactions
    requests.post(f"{BASE_URL}/transactions", json={
        "account_id": acc1_id, "amount": -200, "description": "Uber Ride", 
        "transaction_date": datetime.now().strftime("%Y-%m-%d"), "transaction_type": "expense"
    }, headers=headers)
    
    requests.post(f"{BASE_URL}/transactions", json={
        "account_id": acc1_id, "amount": 5000, "description": "Salary", 
        "transaction_date": datetime.now().strftime("%Y-%m-%d"), "transaction_type": "income"
    }, headers=headers)
    
    # Filter by Type: Income
    resp = requests.get(f"{BASE_URL}/transactions?transaction_type=income", headers=headers)
    incomes = resp.json()
    if len(incomes) == 1 and incomes[0]["description"] == "Salary":
        print_success("Filter by Type (Income) working")
    else:
        print_error(f"Filter by Type failed. Got {len(incomes)} records")
        
    # Filter by Search
    resp = requests.get(f"{BASE_URL}/transactions?search=Grocery", headers=headers)
    search_results = resp.json()
    if len(search_results) == 1 and search_results[0]["description"] == "Grocery Shopping":
        print_success("Filter by Search working")
    else:
        print_error("Filter by Search failed")

    # 6. Test Self-Transfer Detection
    print_step("6. Self-Transfer Detection")
    
    # Create transfer pair
    transfer_amount = 5000
    
    # Debit from Acc1
    requests.post(f"{BASE_URL}/transactions", json={
        "account_id": acc1_id, "amount": -transfer_amount, "description": "Transfer to SBI", 
        "transaction_date": datetime.now().strftime("%Y-%m-%d"), "transaction_type": "expense"
    }, headers=headers)
    
    # Credit to Acc2
    requests.post(f"{BASE_URL}/transactions", json={
        "account_id": acc2_id, "amount": transfer_amount, "description": "Received from HDFC", 
        "transaction_date": datetime.now().strftime("%Y-%m-%d"), "transaction_type": "income"
    }, headers=headers)
    
    # Run detection
    resp = requests.get(f"{BASE_URL}/transfers/detect", headers=headers)
    potentials = resp.json()
    
    if len(potentials) > 0:
        print_success(f"Detected {len(potentials)} potential transfers")
        transfer = potentials[0]
        print(f"   Match: {transfer['debit_transaction']['description']} -> {transfer['credit_transaction']['description']}")
        print(f"   Confidence: {transfer['confidence_score']}")
        
        # Link them
        link_data = {
            "debit_transaction_id": transfer['debit_transaction']['id'],
            "credit_transaction_id": transfer['credit_transaction']['id'],
            "confidence_score": transfer['confidence_score']
        }
        resp = requests.post(f"{BASE_URL}/transfers", json=link_data, headers=headers)
        if resp.status_code == 200:
            print_success("Linked transfer successfully")
        else:
            print_error(f"Failed to link transfer: {resp.text}")
    else:
        print_error("Failed to detect transfer pair")

    # 7. Test Budgets
    print_step("7. Budget Tracking")
    
    # Get categories
    resp = requests.get(f"{BASE_URL}/categories", headers=headers)
    categories = resp.json()
    if not categories:
        # Create a category if none exist
        resp = requests.post(f"{BASE_URL}/categories", json={"name": "Food", "type": "expense"}, headers=headers)
        cat_id = resp.json()["id"]
    else:
        cat_id = categories[0]["id"]
        
    # Create Budget
    budget_amount = 2000
    budget_data = {
        "category_id": cat_id,
        "amount": budget_amount,
        "period": "monthly",
        "month": datetime.now().month,
        "year": datetime.now().year
    }
    resp = requests.post(f"{BASE_URL}/budgets", json=budget_data, headers=headers)
    if resp.status_code == 201:
        print_success(f"Created budget of {budget_amount}")
    else:
        print_error(f"Failed to create budget: {resp.text}")
        
    # Assign transaction to category to test progress
    # Get the grocery transaction id
    resp = requests.get(f"{BASE_URL}/transactions?search=Grocery", headers=headers)
    tx_id = resp.json()[0]["id"]
    
    # Update transaction with category
    requests.put(f"{BASE_URL}/transactions/{tx_id}", json={"category_id": cat_id}, headers=headers)
    
    # Verify update
    resp = requests.get(f"{BASE_URL}/transactions/{tx_id}", headers=headers)
    updated_tx = resp.json()
    print(f"   Updated Transaction Category: {updated_tx.get('category_id')}")
    print(f"   Target Category: {cat_id}")
    
    # Check Budget Progress
    resp = requests.get(f"{BASE_URL}/budgets", headers=headers)
    budgets = resp.json()
    if budgets:
        b = budgets[0]
        print(f"   Budget: {b['amount']}, Spent: {b['spent']}, Remaining: {b['remaining']}")
        if b['spent'] == 1500:
            print_success("Budget progress calculated correctly")
        else:
            print_error(f"Budget progress incorrect. Expected 1500 spent, got {b['spent']}")

    # 8. Test Export
    print_step("8. Data Export")
    resp = requests.get(f"{BASE_URL}/transactions/export/csv", headers=headers)
    if resp.status_code == 200:
        content = resp.text
        lines = content.split('\n')
        if len(lines) > 1 and "Date,Description" in lines[0]:
            print_success(f"Exported CSV successfully ({len(lines)-2} records)") # -2 for header and empty last line
        else:
            print_error("CSV export format incorrect")
    else:
        print_error(f"Export failed: {resp.status_code}")

    # 9. Remaining Endpoints Coverage
    print_step("9. Remaining Endpoints Coverage")

    # 9.1 Auth: Me & Refresh
    resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if resp.status_code == 200 and resp.json()["email"] == EMAIL:
        print_success("Auth: /me endpoint working")
    else:
        print_error("Auth: /me failed")
        
    # Refresh token (assuming we have one, but login response usually returns it)
    # Let's check login response again or just skip if not captured.
    # Login response model is Token(access_token, token_type, refresh_token)
    # But in test_features.py we only captured access_token.
    # Let's re-login to get refresh token
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    refresh_token = resp.json().get("refresh_token")
    if refresh_token:
        resp = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token})
        if resp.status_code == 200 and "access_token" in resp.json():
            print_success("Auth: /refresh endpoint working")
        else:
            print_error("Auth: /refresh failed")
    
    # 9.2 Accounts: Get List, Get One, Update, Delete
    # Get List
    resp = requests.get(f"{BASE_URL}/accounts", headers=headers)
    if resp.status_code == 200 and len(resp.json()) >= 2:
        print_success("Accounts: Get List working")
    
    # Get One
    resp = requests.get(f"{BASE_URL}/accounts/{acc1_id}", headers=headers)
    if resp.status_code == 200 and resp.json()["id"] == acc1_id:
        print_success("Accounts: Get One working")
        
    # Update
    resp = requests.put(f"{BASE_URL}/accounts/{acc1_id}", json={"name": "HDFC Updated"}, headers=headers)
    if resp.status_code == 200 and resp.json()["name"] == "HDFC Updated":
        print_success("Accounts: Update working")
        
    # Delete (We'll delete acc2)
    resp = requests.delete(f"{BASE_URL}/accounts/{acc2_id}", headers=headers)
    if resp.status_code == 204:
        print_success("Accounts: Delete working")
    else:
        print_error(f"Accounts: Delete failed {resp.status_code}")

    # 9.3 Categories: Update, Delete
    # Create a temp category to delete
    resp = requests.post(f"{BASE_URL}/categories", json={"name": "Temp Cat", "type": "expense"}, headers=headers)
    temp_cat_id = resp.json()["id"]
    
    # Update
    resp = requests.put(f"{BASE_URL}/categories/{temp_cat_id}", json={"name": "Temp Cat Updated"}, headers=headers)
    if resp.status_code == 200 and resp.json()["name"] == "Temp Cat Updated":
        print_success("Categories: Update working")
        
    # Delete
    resp = requests.delete(f"{BASE_URL}/categories/{temp_cat_id}", headers=headers)
    if resp.status_code == 204:
        print_success("Categories: Delete working")
        
    # 9.4 Transactions: Delete
    # Create a temp transaction
    resp = requests.post(f"{BASE_URL}/transactions", json={
        "account_id": acc1_id, "amount": -100, "description": "To Delete", 
        "transaction_date": datetime.now().strftime("%Y-%m-%d"), "transaction_type": "expense"
    }, headers=headers)
    del_tx_id = resp.json()["id"]
    
    # Delete
    resp = requests.delete(f"{BASE_URL}/transactions/{del_tx_id}", headers=headers)
    if resp.status_code == 204:
        print_success("Transactions: Delete working")
        
    # 9.5 Transfers: Get List, Delete
    # Get List
    resp = requests.get(f"{BASE_URL}/transfers", headers=headers)
    transfers = resp.json()
    if resp.status_code == 200 and len(transfers) > 0:
        print_success("Transfers: Get List working")
        transfer_id = transfers[0]["id"]
        
        # Delete
        resp = requests.delete(f"{BASE_URL}/transfers/{transfer_id}", headers=headers)
        if resp.status_code == 200:
            print_success("Transfers: Delete working")
    
    # 9.6 Budgets: Update, Delete
    # We have a budget created earlier
    resp = requests.get(f"{BASE_URL}/budgets", headers=headers)
    if resp.json():
        budget_id = resp.json()[0]["id"]
        
        # Update
        resp = requests.put(f"{BASE_URL}/budgets/{budget_id}", json={"amount": 3000}, headers=headers)
        if resp.status_code == 200 and resp.json()["amount"] == 3000:
            print_success("Budgets: Update working")
            
        # Delete
        resp = requests.delete(f"{BASE_URL}/budgets/{budget_id}", headers=headers)
        if resp.status_code == 204:
            print_success("Budgets: Delete working")
            
    # 9.7 Dashboard Stats
    resp = requests.get(f"{BASE_URL}/dashboard", headers=headers)
    if resp.status_code == 200:
        stats = resp.json()
        if "summary" in stats and "total_balance" in stats["summary"]:
            print_success("Dashboard: Stats working")
        else:
            print_error("Dashboard: Stats missing keys")
    else:
        print_error(f"Dashboard: Stats failed {resp.status_code}")

if __name__ == "__main__":
    try:
        test_flow()
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
