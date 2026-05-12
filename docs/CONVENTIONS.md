# Conventions and Standards — Empat.IA

> How code is organized, which standards to follow, and how to add features safely.

---

## Index

1. [Python Standards (FastAPI)](#1-python-standards-fastapi)
2. [React Standards (Frontend)](#2-react-standards-frontend)
3. [How to Add an Endpoint in Gateway](#3-how-to-add-an-endpoint-in-gateway)
4. [How to Add a New Domain Service](#4-how-to-add-a-new-domain-service)
5. [How to Add a New Admin Panel Page](#5-how-to-add-a-new-admin-panel-page)
6. [How to Add a New Web UI Component](#6-how-to-add-a-new-web-ui-component)
7. [Database Standards (MongoDB + Motor)](#7-database-standards-mongodb--motor)
8. [Error Handling](#8-error-handling)
9. [Logging](#9-logging)
10. [Git and Commits](#10-git-and-commits)

---

## 1. Python Standards (FastAPI)

### Formatting

- Follow **PEP 8** and format with **Black**
- Use type hints in all service functions
- Add short docstrings for public functions

### Use Pydantic Models for Requests

Define Pydantic models in `main.py` (or `models/`) for typed request payloads:

```python
class MyRequest(BaseModel):
    required_field: str
    optional_field: Optional[str] = None
    with_default: bool = False
```

Do not use `request: Request` + `await request.json()` for typed payloads. Use that pattern only for truly dynamic schemas.

### Endpoint Structure

```python
@app.post("/api/my-endpoint")
async def my_endpoint(request: MyRequest):
    """One-line description of what this route does."""
    try:
        result = await my_service.do_something(request.required_field)

        if not result:
            raise HTTPException(status_code=404, detail="Resource not found")

        return {
            "success": True,
            "data": result,
        }

    except HTTPException:
        raise  # Re-raise expected HTTP errors
    except Exception as exc:
        logger.error(f"Error processing my endpoint: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Response Pattern

- Success: `{ "success": True, "data": ... }`
- Semantic HTTP error: raise `HTTPException` with proper status + `detail`
- Unexpected error: return 500 with generic message

### Gateway Imports

Add new routers under `src/api/` and include them in `main.py`:

```python
from .api.my_router import router as my_router
app.include_router(my_router)
```

Instantiate new services together with existing ones near the top of `main.py`.

---

## 2. React Standards (Frontend)

### Language and Extensions

- New components can use `.jsx` or `.tsx`
- Prefer `.tsx` for complex props and type safety
- `App.jsx` and lightweight utilities may stay in `.jsx` / `.js`

### Component Structure

```tsx
import React, { useEffect, useState } from "react";
import { someService } from "../../services/api.js";

interface Props {
  username: string;
  onLogout: () => void;
}

export default function MyComponent({ username, onLogout }: Props) {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const response = await someService(username);
      setData(response.data);
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) return <div>Loading...</div>;

  return <div className="...">{/* content */}</div>;
}
```

### Styling

- **Tailwind CSS** utility classes are the default
- Use **MUI** (`@mui/material`) for complex controls like Dialog, Drawer, TextField
- Use **Framer Motion** (web-ui) for entry/exit animations
- Avoid CSS Modules or styled-components to keep consistency with Tailwind

### State

- Use local state via `useState` and `useReducer`
- No Redux (project does not use complex global state)
- `AuthContext` in admin-panel is the only active Context API usage
- Session data is persisted in `localStorage` (see [`FRONTEND.md#5-localstorage`](FRONTEND.md#5-localstorage--chaves-utilizadas))

### API Calls

- All HTTP calls must go through `src/services/api.js`
- Do not call `fetch` or `axios` directly inside components
- Add one `api.js` function per new backend endpoint

---

## 3. How to Add an Endpoint in Gateway

### Step by Step

**1. Define the Pydantic model** (if needed) in `main.py`:

```python
class MyNewRequest(BaseModel):
    session_id: str
    payload: Optional[Dict[str, Any]] = None
```

**2. Add the endpoint** in `main.py` (inline routes) or in a router under `src/api/`:

```python
@app.post("/api/my-feature/{param}")
async def my_new_route(param: str, request: MyNewRequest):
    """Description of this route."""
    try:
        result = await my_service.process(param, request.payload)
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error in my_new_route: {exc}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

**3. Add matching frontend `api.js` function:**

```js
export const myNewFunction = async (param, payload) => {
  const response = await api.post(`/api/my-feature/${param}`, { payload });
  return response.data;
};
```

**4. Update `TECHNICAL.md`** with the new endpoint in API reference.

---

## 4. How to Add a New Domain Service

A domain service is a Python class under `services/gateway-service/src/services/`.

**1. Create file** `src/services/my_service.py`:

```python
from datetime import datetime
import logging

from ..models.database import get_collection

logger = logging.getLogger(__name__)


class MyService:
    async def create(self, data: dict) -> dict:
        """Create a new resource."""
        collection = get_collection("my_collection")

        document = {
            **data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        return document

    async def get_by_id(self, item_id: str) -> dict | None:
        """Get resource by id."""
        collection = get_collection("my_collection")
        return await collection.find_one({"_id": item_id})
```

**2. Instantiate in `main.py`:**

```python
from .services.my_service import MyService

my_service = MyService()
```

**3. Use in endpoints:**

```python
@app.post("/api/my-resource")
async def create_resource(data: dict):
    return await my_service.create(data)
```

---

## 5. How to Add a New Admin Panel Page

**1. Create file** `apps/admin-panel/src/pages/MyPage.js`:

```jsx
import React, { useEffect, useState } from "react";
import { api } from "../services/api";

export default function MyPage() {
  const [data, setData] = useState([]);

  useEffect(() => {
    api.get("/api/admin/my-resource").then((response) => setData(response.data));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Page Title</h1>
      {/* content */}
    </div>
  );
}
```

**2. Add route in `App.js`:**

```jsx
import MyPage from "./pages/MyPage";

// Inside route config:
<Route path="/my-page" element={<MyPage />} />
```

**3. Add sidebar navigation link** in admin navigation component.

---

## 6. How to Add a New Web UI Component

**1. Create file** under `apps/web-ui/src/components/`.

Organize by area (`Chat/`, `Home/`, etc.):

```tsx
// apps/web-ui/src/components/MyComponent.tsx
interface Props {
  title: string;
  onClick: () => void;
}

export default function MyComponent({ title, onClick }: Props) {
  return (
    <button
      onClick={onClick}
      className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
    >
      {title}
    </button>
  );
}
```

**2. Import where needed:**

```jsx
import MyComponent from "../MyComponent";
```

---

## 7. Database Standards (MongoDB + Motor)

### Access collections

```python
from .models.database import get_collection

collection = get_collection("collection_name")
```

### Basic queries

```python
# Find one
doc = await collection.find_one({"field": value})

# Find many
cursor = collection.find({"field": value}).sort("created_at", -1).limit(50)
docs = [doc async for doc in cursor]

# Insert
result = await collection.insert_one({"field": "value", "created_at": datetime.utcnow()})

# Update
await collection.update_one(
    {"_id": item_id},
    {"$set": {"field": new_value, "updated_at": datetime.utcnow()}},
)

# Delete (prefer soft-delete with is_active=False)
await collection.update_one({"_id": item_id}, {"$set": {"is_active": False}})
```

### Critical security rules

**Always include `username` in `messages` and `conversations` filters:**

```python
# CORRECT — per-user isolation
doc = await collection.find_one(
    {
        "session_id": session_id,
        "username": username,  # REQUIRED
    }
)

# WRONG — may return another user's data
doc = await collection.find_one({"session_id": session_id})
```

See therapeutic sessions section in [`TECHNICAL.md`](TECHNICAL.md) for current `chat_id`, `session_id`, and user-isolation patterns.

### ObjectId serialization

MongoDB returns `ObjectId`, which is not JSON-serializable. Convert to string:

```python
document["_id"] = str(document["_id"])
```

Or use a helper:

```python
def serialize_doc(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc
```

### Timestamps

Always use `datetime.utcnow()` for timestamps (not `datetime.now()`):

```python
from datetime import datetime

document = {
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow(),
}
```

---

## 8. Error Handling

### Backend (Python)

```python
try:
    result = await service.operation()

    if not result:
        raise HTTPException(status_code=404, detail="Not found")

    return {"success": True, "data": result}

except HTTPException:
    raise  # Re-raise expected HTTPException
except ValueError as exc:
    raise HTTPException(status_code=400, detail=str(exc))
except Exception as exc:
    logger.error(f"Unexpected error in [function_name]: {exc}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

Never expose internal exception details in production for 500 responses.

### Frontend (React)

```js
const loadData = async () => {
  try {
    setIsLoading(true);
    const response = await someService();
    setData(response.data);
  } catch (err) {
    console.error("Load error:", err);
    // Show visible feedback to user (toast/error message)
    setError("Could not load data. Please try again.");
  } finally {
    setIsLoading(false);
  }
};
```

---

## 9. Logging

### Backend

```python
import logging

logger = logging.getLogger(__name__)

# Severity prefixes used by this project:
logger.info("✅ Operation completed successfully")
logger.warning("⚠️ Unexpected but non-critical condition")
logger.error("❌ Error requiring attention")

# Include relevant context:
logger.info(f"🌐 Processing message: session_id={session_id}, username={username}")
```

Log level is controlled by `LOG_LEVEL` in `.env` (default: `INFO`).

### Frontend

```js
console.error("Processing error:", err); // for errors
// Use console.log only during development and remove before PR
```

---

## 10. Git and Commits

### Conventional Commits

```text
feat: add sentiment analysis endpoint
fix: correct audio_url rewrite in voice proxy
docs: update API reference with new emotion endpoints
refactor: extract session_id logic into helper
chore: update gateway service dependencies
test: add tests for UserTherapeuticSessionService
```

### Branch naming

```text
feature/feature-name
fix/bug-description
docs/what-you-are-documenting
refactor/what-you-are-refactoring
```

### Pull requests

- PRs to `main` trigger full CI/CD pipeline
- Images are built and deployed automatically to GKE Autopilot
- Verify `GET /health/all` in production after deploy

---

*Last updated: April 2026*
