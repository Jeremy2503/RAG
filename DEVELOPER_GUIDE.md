# Developer Guide

## Quick Start for Developers

This guide helps you get started with development on the Multi-Agent RAG system.

---

## Prerequisites

### Required Software
- **Python**: 3.11 or 3.12 (⚠️ NOT 3.14 - has dependency conflicts)
- **Node.js**: 16.x or higher
- **Git**: For version control
- **MongoDB**: Account on MongoDB Atlas (free tier works)
- **OpenAI API**: API key with access to GPT-4 and embeddings

### Recommended Tools
- **VS Code** or **PyCharm** for Python development
- **Postman** or **Thunder Client** for API testing
- **MongoDB Compass** for database viewing
- **React Developer Tools** browser extension

---

## Project Setup (Step-by-Step)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd multi-agent-rag-backup
```

### 2. Backend Setup

#### 2.1 Create Virtual Environment

```bash
cd backend
python -m venv venv
```

#### 2.2 Activate Virtual Environment

**Windows:**
```bash
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

#### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

**Common Issues:**
- If you get `onnxruntime` errors, make sure you're using Python 3.11 or 3.12
- If `chromadb` fails, try: `pip install chromadb==0.4.24`
- If `numpy` errors occur, try: `pip install "numpy<2.0.0,>=1.24.0"`

#### 2.4 Create `.env` File

Create `backend/.env`:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/rag_platform?retryWrites=true&w=majority

# JWT Configuration
SECRET_KEY=your-super-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload Configuration
ALLOWED_EXTENSIONS=.pdf,.docx,.txt,.md,.jpg,.jpeg,.png,.webp,.bmp,.tiff
MAX_FILE_SIZE=10485760

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHROMA_COLLECTION_NAME=policy_documents

# Logging
LOG_LEVEL=INFO
```

**Getting Your API Keys:**

1. **OpenAI API Key:**
   - Go to https://platform.openai.com/api-keys
   - Create new secret key
   - Copy and paste into `.env`

2. **MongoDB URI:**
   - Go to https://www.mongodb.com/cloud/atlas
   - Create free cluster
   - Click "Connect" → "Connect your application"
   - Copy connection string
   - Replace `<username>` and `<password>` with your credentials

3. **SECRET_KEY:**
   - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Or use any random string (at least 32 characters)

#### 2.5 Create Required Directories

```bash
mkdir -p data/chroma
mkdir -p data/uploads
```

#### 2.6 Run the Backend

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:     MongoDB initialized
INFO:     Connected to ChromaDB (collection: policy_documents)
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Frontend Setup

#### 3.1 Navigate to Frontend

Open a **new terminal** (keep backend running):

```bash
cd frontend
```

#### 3.2 Install Dependencies

```bash
npm install
```

**Common Issues:**
- If you get peer dependency errors, try: `npm install --legacy-peer-deps`

#### 3.3 Create `.env` File

Create `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

#### 3.4 Run the Frontend

```bash
npm start
```

**Expected Output:**
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:5173
  On Your Network:  http://192.168.1.x:5173
```

### 4. Initial Setup

#### 4.1 Create Admin User (Optional)

You can create an admin user via the API or MongoDB directly.

**Option 1: Using Python Script**

Create `backend/create_admin.py`:

```python
import asyncio
from app.repositories.mongodb_repo import MongoDBRepository
from app.utils.security import get_password_hash

async def create_admin():
    repo = MongoDBRepository()
    
    admin_user = {
        "email": "admin@example.com",
        "full_name": "Admin User",
        "hashed_password": get_password_hash("admin123"),
        "role": "admin",
        "is_active": True
    }
    
    result = await repo.create_user(admin_user)
    print(f"Admin created with ID: {result.id}")

if __name__ == "__main__":
    asyncio.run(create_admin())
```

Run:
```bash
python create_admin.py
```

#### 4.2 Register Regular User

1. Go to http://localhost:5173/register
2. Fill in registration form
3. Click "Register"
4. Login at http://localhost:5173/login

---

## Development Workflow

### Running in Development Mode

**Terminal 1 (Backend):**
```bash
cd backend
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm start
```

### Code Structure

```
backend/
├── app/
│   ├── agents/           # AI agents and orchestration
│   ├── api/              # API endpoints
│   ├── models/           # Pydantic models
│   ├── repositories/     # Database access
│   ├── services/         # Business logic
│   ├── utils/            # Helper functions
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI app
├── data/                 # Data storage
├── tests/                # Unit tests
└── requirements.txt      # Dependencies

frontend/
├── src/
│   ├── components/       # React components
│   ├── pages/            # Page components
│   ├── services/         # API client
│   ├── styles/           # CSS files
│   ├── utils/            # Helper functions
│   ├── App.js            # Main app
│   └── index.js          # Entry point
└── package.json          # Dependencies
```

---

## Common Development Tasks

### Adding a New Agent

1. **Create agent file**: `backend/app/agents/my_agent.py`

```python
from app.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, llm, chroma_repo, embedding_generator):
        super().__init__(
            name="My Agent",
            description="Handles X type of queries",
            llm=llm,
            chroma_repo=chroma_repo,
            embedding_generator=embedding_generator
        )
    
    async def _get_system_prompt(self) -> str:
        return """
        You are a specialist in X domain.
        Answer questions about X.
        """
    
    async def process(self, query: str, **kwargs):
        documents = await self._retrieve_documents(
            query=query,
            document_type="my_type",
            n_results=5
        )
        response = await self._generate_response(query, documents)
        return {
            "agent": self.name,
            "response": response,
            "sources": documents
        }
```

2. **Register in orchestrator**: `backend/app/agents/graph_orchestrator.py`

```python
# In __init__
self.my_agent = MyAgent(...)

# Add node
workflow.add_node("my_agent", self._my_agent_node)

# Add node method
def _my_agent_node(self, state):
    result = await self.my_agent.process(state["query"])
    return {"agent_responses": [result]}
```

3. **Update coordinator**: `backend/app/agents/coordinator_agent.py`

Add to available agents list in system prompt.

### Adding a New API Endpoint

1. **Create endpoint**: `backend/app/api/my_endpoint.py`

```python
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/my-endpoint", tags=["My Feature"])

@router.get("/")
async def get_items():
    return {"items": []}

@router.post("/")
async def create_item(item: dict):
    return {"created": True}
```

2. **Register router**: `backend/app/main.py`

```python
from app.api import my_endpoint

app.include_router(my_endpoint.router)
```

### Adding a New Frontend Component

1. **Create component**: `frontend/src/components/MyComponent.jsx`

```jsx
import React from 'react';

const MyComponent = ({ data }) => {
  return (
    <div className="my-component">
      <h2>My Component</h2>
      <p>{data}</p>
    </div>
  );
};

export default MyComponent;
```

2. **Add styles**: `frontend/src/styles/global.css`

```css
.my-component {
  background: var(--bg-secondary);
  padding: 20px;
  border-radius: 12px;
}
```

3. **Use in parent**:

```jsx
import MyComponent from './components/MyComponent';

// In your component
<MyComponent data={myData} />
```

---

## Testing

### Backend Testing

#### Run All Tests
```bash
cd backend
pytest
```

#### Run Specific Test
```bash
pytest tests/test_agents.py
```

#### Run with Coverage
```bash
pytest --cov=app tests/
```

#### Example Test

```python
import pytest
from app.agents.hr_policy_agent import HRPolicyAgent

@pytest.mark.asyncio
async def test_hr_agent_query():
    agent = HRPolicyAgent(llm, chroma_repo, embedding_gen)
    
    result = await agent.process("What is the leave policy?")
    
    assert result["agent"] == "HR Policy Agent"
    assert "response" in result
    assert len(result["sources"]) > 0
```

### Frontend Testing

```bash
cd frontend
npm test
```

---

## Debugging

### Backend Debugging

#### Enable Debug Logging

```python
# backend/app/main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### VS Code Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    }
  ]
}
```

#### Common Backend Issues

**Issue**: `ModuleNotFoundError: No module named 'app'`
- **Fix**: Make sure you're in the `backend/` directory

**Issue**: `ImportError: cannot import name 'X'`
- **Fix**: Check for circular imports, verify file names match imports

**Issue**: `401 Unauthorized` on all requests
- **Fix**: Check JWT token is being sent in Authorization header

**Issue**: `ChromaDB collection not found`
- **Fix**: Delete `data/chroma/` and let it recreate on startup

### Frontend Debugging

#### React Developer Tools

1. Install React DevTools browser extension
2. Open browser DevTools
3. Go to "Components" tab
4. Inspect component state and props

#### Console Logging

```jsx
// Add temporary logs
console.log('Component rendered', { props, state });

// Debug API calls
console.log('API Response:', response);
```

#### Common Frontend Issues

**Issue**: `CORS error`
- **Fix**: Make sure backend has CORS enabled for `http://localhost:5173`

**Issue**: API calls fail with 404
- **Fix**: Check `REACT_APP_API_URL` in `.env` is correct

**Issue**: White screen / blank page
- **Fix**: Check browser console for errors, check component imports

---

## Performance Optimization

### Backend Optimization

#### 1. Enable Async Everywhere

```python
# Use async functions
async def my_function():
    result = await async_operation()
    return result
```

#### 2. Batch Database Operations

```python
# Instead of:
for doc in docs:
    await db.insert(doc)

# Do:
await db.insert_many(docs)
```

#### 3. Cache Embeddings

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str):
    return generate_embedding(text)
```

### Frontend Optimization

#### 1. Use React.memo

```jsx
import React, { memo } from 'react';

const MyComponent = memo(({ data }) => {
  return <div>{data}</div>;
});
```

#### 2. Lazy Loading

```jsx
import React, { lazy, Suspense } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HeavyComponent />
    </Suspense>
  );
}
```

---

## Git Workflow

### Branch Naming

- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical fixes for production
- `refactor/` - Code refactoring

Example: `feature/add-new-agent`

### Commit Messages

Follow conventional commits:

```
feat: add new policy agent for finance
fix: resolve authentication token expiry issue
docs: update API documentation
refactor: simplify agent orchestration logic
test: add tests for document upload
```

### Pull Request Process

1. Create feature branch
2. Make changes
3. Test locally
4. Push to remote
5. Create pull request
6. Code review
7. Merge to main

---

## Useful Commands

### Backend

```bash
# Run server
python -m uvicorn app.main:app --reload

# Run tests
pytest

# Check code style
flake8 app/

# Format code
black app/

# Type checking
mypy app/

# Generate requirements
pip freeze > requirements.txt
```

### Frontend

```bash
# Start dev server
npm start

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format
```

### Database

```bash
# MongoDB shell
mongosh "mongodb+srv://cluster..."

# Export data
mongoexport --uri="..." --collection=users --out=users.json

# Import data
mongoimport --uri="..." --collection=users --file=users.json
```

---

## Troubleshooting

### Can't Connect to MongoDB

1. Check MongoDB Atlas IP whitelist
2. Verify connection string in `.env`
3. Test connection with MongoDB Compass

### OpenAI API Errors

1. Check API key is valid
2. Verify you have credits/quota
3. Check rate limits

### ChromaDB Issues

1. Delete `data/chroma/` directory
2. Restart backend
3. Re-upload documents

### Frontend Won't Start

1. Delete `node_modules/`
2. Delete `package-lock.json`
3. Run `npm install` again

---

## Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LangChain Docs](https://python.langchain.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [React Docs](https://react.dev/)
- [ChromaDB Docs](https://docs.trychroma.com/)

### Community
- [LangChain Discord](https://discord.gg/langchain)
- [FastAPI Discord](https://discord.gg/VQjSZaeJmf)
- [React Community](https://react.dev/community)

---

## Need Help?

If you encounter issues not covered here:

1. Check the logs (backend console output)
2. Check browser console (for frontend issues)
3. Search existing issues in the repository
4. Ask the team on Slack/Discord
5. Create a detailed issue report

---

**Happy Coding!** 🚀


