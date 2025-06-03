# Fake Authentication Approach for Quodsi Frontend

## Overview

This document outlines the approach for creating a React+TypeScript frontend with fake authentication that integrates with the existing FastAPI backend. The authentication will be "fake" in that passwords are ignored, but the system will maintain user context for API calls until Microsoft Entra ID integration is implemented.

## Current Backend State

The FastAPI application currently:
- Has complete user/tenant database models via Alembic
- Mocks authentication by assuming a user is signed in
- Retrieves tenant_id from the authenticated user context
- Has registration and user profile endpoints already implemented

## Proposed Frontend Architecture

### Technology Stack
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS (lightweight and modern)
- **State Management**: React Context API + localStorage
- **HTTP Client**: Axios or fetch with custom hooks
- **Routing**: React Router v6

### Authentication Flow Design

#### Registration Flow
1. User fills out registration form (name, email, password)
2. Frontend calls `/api/registration/register` endpoint
3. Backend creates user record (ignoring password for now)
4. Frontend automatically "logs in" the newly created user
5. User context is established with user_id and tenant_id

#### Login Flow
1. User enters email (password field present but ignored)
2. Frontend calls new `/api/auth/fake-login` endpoint with email
3. Backend looks up user by email, returns user info if exists
4. Frontend establishes user context with returned user data
5. Subsequent API calls include user context

### Required Backend Modifications

#### New Authentication Endpoints

```python
# app/api/routers/auth.py (new file)

@router.post("/fake-login")
async def fake_login(
    email: str,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Fake login - just lookup user by email, no password validation
    """
    user = await user_service.get_user_by_email(email, db)
    if not user:
        raise HTTPException(404, "User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        tenant_id=user.tenant_id,
        status=user.status
    )

@router.get("/me")
async def get_current_user(
    user_id: str,  # From request header or query param
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get current user info for maintaining session
    """
    user = await user_service.get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(404, "User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        tenant_id=user.tenant_id,
        status=user.status
    )
```

#### Modified API Client Pattern

All API calls will include user context via headers:

```typescript
// In frontend API client
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'X-User-ID': currentUser?.id,
    'X-Tenant-ID': currentUser?.tenant_id,
  },
});
```

### Frontend Component Structure

```
src/
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   └── AuthLayout.tsx
│   ├── dashboard/
│   │   ├── Dashboard.tsx
│   │   └── UserInfo.tsx
│   └── common/
│       ├── Header.tsx
│       └── Layout.tsx
├── contexts/
│   └── AuthContext.tsx
├── hooks/
│   ├── useAuth.ts
│   └── useApi.ts
├── services/
│   └── api.ts
├── types/
│   └── user.ts
└── App.tsx
```

### User Context Management

```typescript
// types/user.ts
interface User {
  id: string;
  email: string;
  display_name: string;
  tenant_id: string;
  status: string;
}

// contexts/AuthContext.tsx
interface AuthContextType {
  user: User | null;
  login: (email: string) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}
```

### Persistent Authentication State

The app will maintain authentication state across browser sessions using localStorage, providing a seamless user experience.

#### Auto-Login on App Restart

**User Experience Flow:**
1. User logs in → user data stored in localStorage
2. User closes browser/app
3. User reopens app → automatically "logged in" from stored data
4. User sees dashboard immediately (no re-login required)

**Implementation (Low Effort - ~15-20 lines of code):**

```typescript
// In AuthContext.tsx
const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Loading state during startup

  // Auto-login on app startup
  useEffect(() => {
    const restoreUserSession = async () => {
      try {
        const storedUser = localStorage.getItem('quodsi_user');
        if (storedUser) {
          const userData = JSON.parse(storedUser);
          
          // Optional: Verify user still exists in backend
          const response = await api.get(`/auth/me?user_id=${userData.id}`);
          if (response.data) {
            setUser(userData);
          } else {
            // User no longer exists, clear storage
            localStorage.removeItem('quodsi_user');
          }
        }
      } catch (error) {
        // If error, clear potentially corrupted storage
        localStorage.removeItem('quodsi_user');
      } finally {
        setIsLoading(false);
      }
    };

    restoreUserSession();
  }, []);

  const login = async (email: string) => {
    const response = await api.post('/auth/fake-login', { email });
    const userData = response.data;
    
    setUser(userData);
    localStorage.setItem('quodsi_user', JSON.stringify(userData)); // Store for persistence
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('quodsi_user'); // Clear storage
  };

  // Show loading spinner while checking storage on startup
  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};
```

#### Additional Persistence Features (Optional)

- **Session Expiration**: Add timestamp to stored data (e.g., 30-day expiration)
- **Data Validation**: Verify stored user data structure on restore
- **Graceful Fallback**: Handle corrupted localStorage gracefully
- **Multiple Tabs**: Sync login/logout across browser tabs using `storage` events

#### Storage Structure

```typescript
// localStorage key: 'quodsi_user'
interface StoredUser {
  id: string;
  email: string;
  display_name: string;
  tenant_id: string;
  status: string;
  loginTimestamp?: number; // For optional expiration
}
```

This provides a modern web app experience where users remain "logged in" across sessions while requiring minimal implementation effort.

### UI Components

#### Login Form
- Email input (required)
- Password input (present but ignored)
- "Sign In" button
- Link to registration form
- Simple validation and error handling

#### Registration Form
- Full name input
- Email input
- Password input (ignored but collected for future Entra integration)
- "Create Account" button
- Link back to login form
- Form validation

#### Dashboard
- Display current user information
- Show tenant details
- Navigation to future model management features
- Logout functionality

### Migration Path to Microsoft Entra

When ready to implement Entra:

1. Replace fake login endpoint with Entra OAuth flow
2. Update frontend to use Entra authentication library
3. Modify user context to include Entra tokens
4. Update API client to use Bearer tokens instead of headers
5. Remove fake authentication endpoints

### Implementation Steps

1. **Backend Changes**:
   - Add `app/api/routers/auth.py` with fake login endpoints
   - Modify existing registration endpoint if needed
   - Update main.py to include auth router

2. **Frontend Setup**:
   - Create Vite React+TypeScript project
   - Install dependencies (React Router, Tailwind, Axios)
   - Set up basic project structure

3. **Authentication Implementation**:
   - Create AuthContext and localStorage persistence
   - Build login and registration forms
   - Implement API client with user context headers

4. **Dashboard Creation**:
   - Simple dashboard showing user/tenant info
   - Navigation structure for future features
   - Logout functionality

5. **Integration Testing**:
   - Test registration flow end-to-end
   - Test login flow with existing users
   - Verify API calls include proper user context

### Benefits of This Approach

- **Realistic UX**: Users experience normal login/registration flow
- **Easy Migration**: Simple to swap fake auth for real Entra later
- **Backend Compatible**: Works with existing FastAPI structure
- **Development Friendly**: No external auth dependencies during development
- **User Context**: Establishes proper user/tenant context for all API calls

### Security Considerations

- This is explicitly for development/demo purposes only
- No real authentication or authorization
- Not suitable for production without Entra integration
- User data stored in plain text in localStorage (acceptable for fake auth)

This approach provides a complete authentication experience while maintaining simplicity and preparing for eventual Entra integration.