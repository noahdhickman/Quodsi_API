# Module 7.2a: Registration Endpoint Manual Testing Procedures

## Purpose
Comprehensive manual testing guide for registration endpoints using curl commands, designed for interns to learn API testing fundamentals.

## Prerequisites
- Completed Module 7.2 (Registration Endpoint Implementation)
- FastAPI server running on `http://localhost:8000`
- curl installed on your system
- Basic understanding of HTTP methods and JSON

---

## Understanding curl for API Testing

### What is curl?
curl (Client URL) is a command-line tool for transferring data to/from servers. It's perfect for testing APIs because:
- **Simple**: Easy to use from command line
- **Versatile**: Supports all HTTP methods (GET, POST, PUT, DELETE)
- **Headers**: Can set custom headers (authentication, content-type)
- **Data**: Can send JSON data in request body
- **Output**: Shows both request and response details

### 🚨 CRITICAL: Terminal Type Matters!

**The backslash (`\`) line continuation in our examples ONLY works in bash/Linux terminals.**

**If you're using PowerShell (default in VS Code on Windows):**
- Multi-line commands with `\` **DON'T WORK** ❌
- You'll get errors like `-H is not recognized`

**If you're using Command Prompt (cmd):**
- Multi-line commands with `\` **DON'T WORK** either ❌

### How to Check Which Terminal You're Using

Look at your terminal prompt:
- **PowerShell**: `PS C:\your\path>` 
- **Command Prompt**: `C:\your\path>`
- **Git Bash**: `user@computer MINGW64 /c/your/path $`

### 🔧 PowerShell Solutions (Most Common)

**If you see `PS C:\your\path>` you're using PowerShell. Use ONE of these solutions:**

#### Solution 1: Single Quotes for JSON (Easiest & Most Reliable)
```powershell
# Use SINGLE quotes around the JSON data - no escaping needed!
curl -X POST "http://localhost:8000/api/registration/tenant" -H "Content-Type: application/json" -d '{"name": "Test Company", "domain": "testco", "admin_email": "admin@testco.com", "admin_password": "securepass123", "admin_display_name": "Test Admin"}'
```

#### Solution 2: PowerShell Here-String (Multi-line)
```powershell
# Define JSON in a variable first
$json = @'
{"name": "Test Company", "domain": "testco", "admin_email": "admin@testco.com", "admin_password": "securepass123", "admin_display_name": "Test Admin"}
'@

# Then use the variable
curl -X POST "http://localhost:8000/api/registration/tenant" -H "Content-Type: application/json" -d $json
```

#### Solution 3: Switch to Command Prompt
```cmd
# Open Command Prompt instead
# Press Win+R, type "cmd", press Enter
# Navigate to your project directory
cd C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api
# Then use single-line commands like Solution 1
```

---

## Pre-Testing Setup

### Step 1: Start Your FastAPI Server
```bash
# Navigate to your project directory
cd C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api

# Start the server
uvicorn app.main:app --reload

# You should see output like:
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process [xxxxx]
```

### Step 2: Set Up Your Testing Terminal

**⚠️ IMPORTANT: Do NOT run curl commands in the same terminal as your server!**

You need **TWO separate terminals**:
- **Terminal 1**: Running your FastAPI server (uvicorn)
- **Terminal 2**: Running your curl test commands

#### Option A: New VS Code Terminal Tab (Recommended)

If you're using VS Code (which you should be):

1. **Keep Terminal 1 running your server** - Don't close it!

2. **Open a second terminal tab** in VS Code:
   - Press `Ctrl + Shift + `` (backtick) **OR**
   - Click `Terminal` → `New Terminal` **OR** 
   - Click the `+` button next to your existing terminal tab

3. **You should now see two terminal tabs**:
   ```
   Terminal Tabs: [bash ✓] [bash] 
                    ↑        ↑
               Server    Testing
   ```

4. **In Terminal 2 (your new testing terminal)**:
   ```bash
   # Make sure you're in the right directory
   pwd
   # Should show: C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api
   
   # If not, navigate there:
   cd C:\_source\Greenshoes\Summer2025Internship\Sprint2\Guided_Walkthrough\quodsi_api
   ```

### Step 3: Test Basic Connectivity

**Choose the right command for your terminal type:**

#### For PowerShell (PS C:\path>):
```powershell
# Single line version
curl http://localhost:8000/
```

#### For Command Prompt (C:\path>) or Git Bash:
```bash
curl http://localhost:8000/
```

**Expected response**:
```json
{
  "message": "Welcome to Quodsi API",
  "status": "running",
  "version": "0.1.0",
  "environment": "development"
}
```

---

## Test Suite: Tenant Registration

### Test 1: Successful Tenant Registration

**For PowerShell Users (Most Common):**
```powershell
# Single quotes around JSON - copy this exact line
curl -X POST "http://localhost:8000/api/registration/tenant" -H "Content-Type: application/json" -d '{"name": "Acme Corporation", "domain": "acme", "admin_email": "admin@acme.com", "admin_password": "securepass123", "admin_display_name": "John Admin"}'
```

**For Command Prompt Users:**
```cmd
curl -X POST "http://localhost:8000/api/registration/tenant" -H "Content-Type: application/json" -d "{\"name\": \"Acme Corporation\", \"domain\": \"acme\", \"admin_email\": \"admin@acme.com\", \"admin_password\": \"securepass123\", \"admin_display_name\": \"John Admin\"}"
```

**For Git Bash Users (Multi-line works):**
```bash
curl -X POST "http://localhost:8000/api/registration/tenant" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Acme Corporation",
       "domain": "acme", 
       "admin_email": "admin@acme.com",
       "admin_password": "securepass123",
       "admin_display_name": "John Admin"
     }'
```

**Expected Response** (Status: 200):
```json
{
  "data": {
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_name": "Acme Corporation",
    "domain": "acme",
    "admin_user_id": "123e4567-e89b-12d3-a456-426614174000",
    "admin_email": "admin@acme.com",
    "message": "Tenant and admin user registered successfully"
  },
  "meta": {
    "timestamp": "2025-01-28T10:30:45.123456",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**📝 IMPORTANT: Save these IDs for later tests!**
- `tenant_id`: 550e8400-e29b-41d4-a716-446655440000
- `admin_user_id`: 123e4567-e89b-12d3-a456-426614174000

### Test 2: Password Validation Error

**For PowerShell:**
```powershell
curl -X POST "http://localhost:8000/api/registration/tenant" -H "Content-Type: application/json" -d '{"name": "Test Company", "domain": "testco", "admin_email": "admin@testco.com", "admin_password": "short", "admin_display_name": "Test Admin"}'
```

**Expected Response** (Status: 422):
```json
{
  "meta": {
    "timestamp": "2025-01-28T10:45:00.000000"
  },
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Password must be at least 8 characters",
      "field": "admin_password"
    }
  ]
}
```

### Test 3: Duplicate Domain Error

**For PowerShell (use same domain as Test 1):**
```powershell
curl -X POST "http://localhost:8000/api/registration/tenant" -H "Content-Type: application/json" -d '{"name": "Another Acme", "domain": "acme", "admin_email": "different@acme.com", "admin_password": "password123", "admin_display_name": "Different Admin"}'
```

**Expected Response** (Status: 409):
```json
{
  "meta": {
    "timestamp": "2025-01-28T10:40:15.789012"
  },
  "errors": [
    {
      "code": "DUPLICATE_ERROR",
      "message": "Tenant domain or admin email already exists"
    }
  ]
}
```

---

## Test Suite: User Registration

### Test 4: Successful User Registration

**For PowerShell (use IDs from Test 1):**
```powershell
curl -X POST "http://localhost:8000/api/registration/user" -H "Content-Type: application/json" -H "X-Mock-Tenant-Id: 550e8400-e29b-41d4-a716-446655440000" -H "X-Mock-User-Id: 123e4567-e89b-12d3-a456-426614174000" -H "X-Mock-Email: admin@acme.com" -H "X-Mock-Display-Name: John Admin" -d '{"email": "employee@acme.com", "password": "userpass123", "display_name": "Alice Employee", "role": "user"}'
```

**Expected Response** (Status: 200):
```json
{
  "data": {
    "user_id": "789e0123-e89b-12d3-a456-426614174001",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "employee@acme.com",
    "display_name": "Alice Employee",
    "message": "User registered successfully"
  },
  "meta": {
    "timestamp": "2025-01-28T11:00:00.000000",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Test 5: User Registration Without Mock Headers

**For PowerShell:**
```powershell
curl -X POST "http://localhost:8000/api/registration/user" -H "Content-Type: application/json" -d "{\"email\": \"noauth@test.com\", \"password\": \"password123\", \"display_name\": \"No Auth User\", \"role\": \"user\"}"
```

**Expected**: Should use default test user context from the mock authentication system.

---

## Troubleshooting Common Issues

### Issue 1: `-H is not recognized` Error
```
-H: The term '-H' is not recognized as a name of a cmdlet, function, script file, or executable program.
```
**Problem**: You're using PowerShell with bash-style line continuation (`\`)

**Solution**: Use one of the PowerShell solutions above (single-line or backtick continuation)

### Issue 2: `Field required` Error
```json
{"detail":[{"type":"missing","loc":["body"],"msg":"Field required","input":null}]}
```
**Problem**: Your JSON data isn't being sent properly

**Solution**: 
- Make sure you have `Content-Type: application/json` header
- Check that your JSON is properly escaped
- For PowerShell, use `\"` for quotes inside the JSON string

### Issue 3: Connection Refused
```
curl: (7) Failed to connect to localhost port 8000: Connection refused
```
**Solution**: Make sure your FastAPI server is running in Terminal 1

### Issue 4: 404 Not Found
```json
{"detail": "Not Found"}
```
**Solution**: Check your URL path - should be `/api/registration/tenant`

---

## Quick Reference Commands

**Copy-paste ready PowerShell commands:**

### Tenant Registration (Success):
```powershell
curl -X POST "http://localhost:8000/api/registration/tenant" -H "Content-Type: application/json" -d '{"name": "My Company", "domain": "myco", "admin_email": "admin@myco.com", "admin_password": "password123", "admin_display_name": "Admin User"}'
```

### User Registration (Success):
```powershell
curl -X POST "http://localhost:8000/api/registration/user" -H "Content-Type: application/json" -H "X-Mock-Tenant-Id: YOUR_TENANT_ID" -H "X-Mock-User-Id: YOUR_USER_ID" -d '{"email": "user@myco.com", "password": "userpass123", "display_name": "Regular User", "role": "user"}'
```

### Basic Connectivity Test:
```powershell
curl http://localhost:8000/
```

---

## Testing Checklist

- [ ] ✅ Basic connectivity test passes
- [ ] ✅ Successful tenant registration  
- [ ] ❌ Password too short validation
- [ ] ❌ Duplicate domain validation
- [ ] ✅ Successful user registration
- [ ] ✅ User registration without mock headers

---

## Summary

This guide provides PowerShell-specific instructions for interns using Windows with VS Code (the most common setup). The key differences:

1. **PowerShell doesn't support `\` line continuation** - use single lines or backticks
2. **JSON strings need proper escaping** - use `\"` inside double quotes
3. **Multiple terminal management** is crucial for API testing

Continue to the next module:
- **Module 7.3**: User Profile Endpoints → `073_User_Profile_Endpoints.md`
