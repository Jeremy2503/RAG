# Quick Setup Guide

Get the Multi-Agent RAG Platform running in 10 minutes!

## 🎯 Prerequisites Checklist

Before you begin, ensure you have:

- [ ] Python 3.10 or higher installed
- [ ] Node.js 18 or higher installed
- [ ] MongoDB installed locally OR MongoDB Atlas account
- [ ] OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- [ ] Git installed
- [ ] Code editor (VS Code recommended)

## 🚀 Quick Start (3 Steps)

### Step 1: Setup Backend (5 minutes)

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies (this may take a few minutes)
pip install -r requirements.txt

# Create environment file
cp .env.template .env

# IMPORTANT: Edit .env file with your settings
# At minimum, update these:
# - OPENAI_API_KEY=your_actual_key_here
# - MONGODB_URL=mongodb://localhost:27017  (or your MongoDB Atlas URL)
# - JWT_SECRET_KEY=generate_a_strong_random_key
```

**Generate a secure JWT secret key:**
```python
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
Copy the output and paste it as your `JWT_SECRET_KEY` in `.env`

### Step 2: Setup Frontend (2 minutes)

Open a **new terminal window** (keep backend terminal open):

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# (Optional) Create .env file for custom API URL
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env
```

### Step 3: Run the Application (1 minute)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m app.main
```
jeremyj2030_db_user
jQkVvUiDtotu1sGt

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.0.8  ready in 500 ms
  ➜  Local:   http://localhost:5173/
```

**🎉 Done! Open http://localhost:5173 in your browser**

---

## 👤 Create Your First User

### Option 1: Using API (Recommended)

**Create Admin User:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin@123456",
    "full_name": "Admin User",
    "role": "admin"
  }'
```

**Create Regular User:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "User@123456",
    "full_name": "Regular User",
    "role": "user"
  }'
```

### Option 2: Using Python Script

Create `create_users.py`:
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Create admin
admin_data = {
    "email": "admin@example.com",
    "password": "Admin@123456",
    "full_name": "Admin User",
    "role": "admin"
}

# Create user
user_data = {
    "email": "user@example.com",
    "password": "User@123456",
    "full_name": "Regular User",
    "role": "user"
}

for user in [admin_data, user_data]:
    response = requests.post(f"{BASE_URL}/auth/register", json=user)
    if response.status_code == 201:
        print(f"✓ Created {user['role']}: {user['email']}")
    else:
        print(f"✗ Error: {response.json()}")
```

Run it:
```bash
python create_users.py
```

---

## 🧪 Test the System

### 1. Login as Admin
- Go to http://localhost:5173/login/admin
- Email: `admin@example.com`
- Password: `Admin@123456`

### 2. Upload a Test Document
- Click "Upload Documents" tab
- Create a test file (`test_policy.txt`):
  ```
  IT Security Policy
  
  All employees must use strong passwords containing at least 12 characters,
  including uppercase, lowercase, numbers, and special characters.
  
  Passwords must be changed every 90 days.
  ```
- Select document type: "IT Policy"
- Upload the file

### 3. Test the Chat
- Click "Chat & Query" tab
- Ask: "What is the password policy?"
- Watch the multi-agent system respond!

### 4. Test as Regular User
- Logout
- Go to http://localhost:5173/login/user
- Login with: `user@example.com` / `User@123456`
- Ask questions (but cannot upload documents)

---

## 📁 Project Structure

```
multi-agent-rag-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration
│   │   ├── api/                 # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   └── documents.py
│   │   ├── agents/              # Multi-agent system
│   │   │   ├── coordinator_agent.py
│   │   │   ├── it_policy_agent.py
│   │   │   ├── hr_policy_agent.py
│   │   │   ├── research_agent.py
│   │   │   └── graph_orchestrator.py
│   │   ├── services/            # Business logic
│   │   ├── repositories/        # Data access
│   │   ├── models/              # Data models
│   │   └── utils/               # Utilities
│   ├── requirements.txt
│   └── .env                     # Configuration (create from template)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app
│   │   ├── pages/               # Page components
│   │   │   ├── AdminLogin.jsx
│   │   │   ├── UserLogin.jsx
│   │   │   ├── AdminDashboard.jsx
│   │   │   └── UserDashboard.jsx
│   │   ├── components/          # Reusable components
│   │   │   ├── Chat/
│   │   │   └── DocumentUpload.jsx
│   │   ├── context/             # React context
│   │   ├── services/            # API client
│   │   └── styles/              # CSS styles
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## 🔧 Configuration Details

### MongoDB Setup

**Local MongoDB:**
```bash
# Install MongoDB (Ubuntu/Debian)
sudo apt-get install mongodb

# Start MongoDB
sudo systemctl start mongodb

# Verify it's running
mongosh
```

**MongoDB Atlas (Cloud):**
1. Sign up at https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Get connection string
4. Update `.env`: `MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/rag_platform`

### OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy and paste into `.env`: `OPENAI_API_KEY=sk-...`
4. Ensure you have credits in your OpenAI account

### Environment Variables Explained

```env
# Application
DEBUG=True                    # Set to False in production
ENVIRONMENT=development       # Change to 'production' when deploying

# Server
HOST=0.0.0.0                 # Bind to all interfaces
PORT=8000                    # Backend port

# Database
MONGODB_URL=mongodb://localhost:27017    # MongoDB connection
MONGODB_DB_NAME=rag_platform             # Database name

# Vector Store
CHROMA_PERSIST_DIRECTORY=./data/chroma   # Where vectors are stored

# OpenAI
OPENAI_API_KEY=sk-...        # Your OpenAI API key
OPENAI_MODEL=gpt-4-turbo-preview        # Model to use

# Authentication
JWT_SECRET_KEY=<random-key>  # Strong random string
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60      # Token expiry

# CORS
CORS_ORIGINS=http://localhost:5173      # Frontend URL
```

---

## 🐛 Troubleshooting

### Backend won't start

**Error: "ModuleNotFoundError"**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Error: "MongoDB connection failed"**
```bash
# Check if MongoDB is running
mongosh

# If not running, start it
sudo systemctl start mongodb

# Or use MongoDB Atlas URL in .env
```

**Error: "OpenAI API key invalid"**
- Verify your API key at https://platform.openai.com/api-keys
- Check you have credits in your OpenAI account
- Ensure no extra spaces in `.env` file

### Frontend won't start

**Error: "Cannot find module"**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Error: "Port 5173 already in use"**
```bash
# Kill process on port 5173
# On Linux/Mac:
lsof -ti:5173 | xargs kill -9

# On Windows:
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### CORS Errors

- Check `CORS_ORIGINS` in backend `.env` matches frontend URL exactly
- Include port number: `http://localhost:5173`
- Restart backend after changing `.env`

### Database Issues

**ChromaDB errors:**
```bash
# Delete and recreate ChromaDB
rm -rf backend/data/chroma
# Restart backend - it will recreate the database
```

**MongoDB errors:**
```bash
# Check MongoDB is accessible
mongosh mongodb://localhost:27017

# If using Atlas, test connection string
mongosh "mongodb+srv://user:pass@cluster.mongodb.net/test"
```

---

## 📚 Next Steps

1. **Explore the API**
   - Visit http://localhost:8000/docs for interactive API documentation

2. **Upload More Documents**
   - Add HR policy documents
   - Add IT policy documents
   - Test different document types

3. **Test Different Queries**
   - Try IT-related questions
   - Try HR-related questions
   - Test the agent routing

4. **Customize**
   - Modify agent prompts in `backend/app/agents/`
   - Adjust UI styling in `frontend/src/styles/`
   - Configure models in `.env`

5. **Deploy**
   - See `DEPLOYMENT.md` for production deployment guide

---

## 🆘 Getting Help

- **Documentation**: See README.md for detailed documentation
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **GitHub Issues**: Report bugs or request features

---

## 🎓 Learning Resources

**FastAPI:**
- https://fastapi.tiangolo.com/

**LangChain & LangGraph:**
- https://python.langchain.com/docs/
- https://langchain-ai.github.io/langgraph/

**React:**
- https://react.dev/

**OpenAI API:**
- https://platform.openai.com/docs/

---

**Happy Coding! 🚀**

Built with ❤️ using FastAPI, React, LangGraph, and OpenAI

