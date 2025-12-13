# Multi-Agent RAG System with LangGraph

## 📋 Project Overview

A sophisticated **Multi-Agent Retrieval-Augmented Generation (RAG)** system built with LangGraph, featuring intelligent document processing, OCR capabilities, and specialized AI agents for handling domain-specific queries about IT and HR policies.

### Key Features

- 🤖 **Multi-Agent Architecture**: Specialized agents (IT Policy, HR Policy, Research) coordinated by LangGraph
- 🔍 **Intelligent Query Routing**: Coordinator agent routes queries to appropriate specialist agents
- 📄 **Document Processing**: Supports PDFs, DOCX, TXT, MD, and image files (JPG, PNG, WEBP, BMP, TIFF)
- 🖼️ **OCR Integration**: Extract text from images using EasyOCR
- 💾 **Vector Database**: ChromaDB for semantic search and retrieval
- 🔐 **Authentication & Authorization**: User and admin roles with JWT-based auth
- 🎨 **Modern UI**: Dark-themed React interface with purple accents
- 💬 **Chat History**: Persistent conversation storage with MongoDB
- ⚡ **Parallel Execution**: LangGraph enables parallel agent processing for improved performance

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  User Login  │  │ Chat Interface│  │ Doc Upload   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────┴────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              LangGraph Orchestrator                       │  │
│  │  ┌────────────┐    ┌──────────────────────────────┐     │  │
│  │  │Coordinator │───>│  Parallel Agent Executor      │     │  │
│  │  │   Agent    │    │  ┌────┐  ┌────┐  ┌────┐     │     │  │
│  │  └────────────┘    │  │ IT │  │ HR │  │Res.│     │     │  │
│  │                    │  └────┘  └────┘  └────┘     │     │  │
│  │                    └──────────────────────────────┘     │  │
│  │                              │                           │  │
│  │                    ┌──────────▼────────────┐            │  │
│  │                    │  Synthesis Node       │            │  │
│  │                    └───────────────────────┘            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────┐  ┌────────▼──────┐  ┌──────────────┐       │
│  │   MongoDB    │  │   ChromaDB    │  │  OpenAI API  │       │
│  │ (Chat/Users) │  │ (Embeddings)  │  │(LLM/Embeddings)│      │
│  └──────────────┘  └───────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Workflow (LangGraph)

```
User Query
    │
    ▼
┌───────────────┐
│  Coordinator  │ ◄─── Analyzes query & routes to agents
└───────┬───────┘
        │
        ▼
┌────────────────────────────┐
│  Parallel Agent Executor   │
│  ┌──────┐ ┌──────┐ ┌────┐ │
│  │  IT  │ │  HR  │ │Res.│ │ ◄─── Agents run in parallel
│  └──────┘ └──────┘ └────┘ │
└────────────┬───────────────┘
             │
             ▼
     ┌───────────────┐
     │  Synthesizer  │ ◄─── Combines agent responses
     └───────┬───────┘
             │
             ▼
      Final Response
```

---

## 🛠️ Technologies Used

### Backend
- **FastAPI** - Modern, high-performance web framework
- **LangGraph** - Stateful, multi-agent orchestration
- **LangChain** - Individual agent implementations
- **OpenAI API** - LLM (GPT-4) and embeddings (text-embedding-3-small)
- **ChromaDB** - Vector database for semantic search
- **MongoDB** - NoSQL database for chat history and user data
- **EasyOCR** - Optical Character Recognition for images
- **PyPDF2 / python-docx** - Document text extraction
- **Pydantic** - Data validation and settings management
- **JWT** - Authentication tokens

### Frontend
- **React.js** - UI library
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **CSS3** - Modern styling with glassmorphism effects

---

## ✨ Features

### 1. Multi-Agent System
- **Coordinator Agent**: Analyzes queries and routes to appropriate specialist agents
- **IT Policy Agent**: Handles queries about IT security, infrastructure, software, hardware
- **HR Policy Agent**: Handles queries about HR policies, benefits, leave, compensation
- **Research Agent**: Handles general queries that don't fit specific domains

### 2. Document Processing
- **Supported Formats**: 
  - Documents: PDF, DOCX, TXT, MD
  - Images: JPG, JPEG, PNG, WEBP, BMP, TIFF
- **OCR Extraction**: Automatically extracts text from images
- **Smart Chunking**: Splits documents into 500-character chunks with 50-character overlap
- **Junk Filtering**: Filters out short chunks (< 100 chars) like headers/footers at upload and query time
- **Embeddings**: Generates vector embeddings using OpenAI's text-embedding-3-small

### 3. Semantic Search
- **ChromaDB Integration**: Stores and retrieves document embeddings
- **Metadata Filtering**: Filter by document type (it_policy, hr_policy, research)
- **Hybrid Search**: Combines semantic similarity with metadata filters
- **Runtime Filtering**: Filters out junk chunks at query time for better results

### 4. Chat System
- **Persistent History**: Stores conversations in MongoDB
- **Session Management**: Create, view, and switch between chat sessions
- **Message Threading**: Maintains conversation context
- **Source Attribution**: Shows which documents were used to generate responses

### 5. User Management
- **Role-Based Access**: User and Admin roles
- **JWT Authentication**: Secure token-based authentication
- **User Registration**: Self-service account creation
- **Admin Panel**: Admin-only document management

### 6. Modern UI
- **Dark Theme**: Purple/violet accent colors
- **Glassmorphism**: Subtle transparency and blur effects
- **Responsive Design**: Works on desktop and mobile
- **Smooth Animations**: Animated background orbs and transitions
- **Fixed Input Bar**: Chat input stays at bottom while messages scroll
- **Independent Scrolling**: Chat history sidebar scrolls independently

---

## 📁 Project Structure

```
multi-agent-rag-backup/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── base_agent.py              # Base class for all agents
│   │   │   ├── coordinator_agent.py       # Query routing agent
│   │   │   ├── hr_policy_agent.py         # HR specialist agent
│   │   │   ├── it_policy_agent.py         # IT specialist agent
│   │   │   ├── research_agent.py          # General research agent
│   │   │   └── graph_orchestrator.py      # LangGraph workflow
│   │   ├── api/
│   │   │   ├── auth.py                    # Authentication endpoints
│   │   │   ├── chat.py                    # Chat endpoints
│   │   │   └── documents.py               # Document upload endpoints
│   │   ├── models/
│   │   │   ├── chat.py                    # Chat message models
│   │   │   ├── document.py                # Document models
│   │   │   └── user.py                    # User models
│   │   ├── repositories/
│   │   │   ├── chroma_repo.py             # ChromaDB operations
│   │   │   └── mongodb_repo.py            # MongoDB operations
│   │   ├── services/
│   │   │   ├── agent_service.py           # Agent orchestration service
│   │   │   ├── auth_service.py            # Authentication service
│   │   │   ├── chat_service.py            # Chat service
│   │   │   └── document_service.py        # Document processing service
│   │   ├── utils/
│   │   │   ├── embeddings.py              # Embedding generation
│   │   │   ├── security.py                # Password hashing, JWT
│   │   │   └── validators.py              # Input validation
│   │   ├── config.py                      # Configuration settings
│   │   └── main.py                        # FastAPI application
│   ├── data/
│   │   ├── chroma/                        # ChromaDB persistence
│   │   └── uploads/                       # Uploaded documents
│   ├── requirements.txt                   # Python dependencies
│   ├── .env                               # Environment variables
│   └── README.md
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   │   ├── ChatHistory.jsx        # Chat session list
│   │   │   │   ├── ChatInterface.jsx      # Main chat UI
│   │   │   │   └── MessageBubble.jsx      # Individual message
│   │   │   ├── DocumentUpload.jsx         # Document upload component
│   │   │   └── ProtectedRoute.jsx         # Auth guard
│   │   ├── pages/
│   │   │   ├── AdminLogin.jsx             # Admin login page
│   │   │   ├── UserDashboard.jsx          # Main dashboard
│   │   │   ├── UserLogin.jsx              # User login page
│   │   │   └── UserRegister.jsx           # User registration page
│   │   ├── services/
│   │   │   └── api.js                     # API client
│   │   ├── styles/
│   │   │   └── global.css                 # Global styles
│   │   ├── utils/
│   │   │   └── auth.js                    # Auth utilities
│   │   ├── App.js                         # Main React component
│   │   └── index.js                       # Entry point
│   ├── package.json
│   └── README.md
│
└── README.md                              # This file
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.11 or 3.12 (not 3.14 - dependency issues)
- Node.js 16+
- MongoDB Atlas account (or local MongoDB)
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Create `.env` file:**
```env
# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB
MONGODB_URI=your_mongodb_connection_string_here

# JWT
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
ALLOWED_EXTENSIONS=.pdf,.docx,.txt,.md,.jpg,.jpeg,.png,.webp,.bmp,.tiff
MAX_FILE_SIZE=10485760

# ChromaDB
CHROMA_PERSIST_DIRECTORY=./data/chroma
```

6. **Run the backend:**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Create `.env` file:**
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

4. **Run the frontend:**
```bash
npm start
```

Frontend will be available at: `http://localhost:5173`

---

## 📖 Usage

### 1. User Registration
- Navigate to `http://localhost:5173/register`
- Fill in your details and create an account

### 2. Login
- Navigate to `http://localhost:5173/login`
- Enter your credentials
- Admin login available at `/admin/login`

### 3. Upload Documents
- Click the upload icon in the dashboard
- Select PDF, DOCX, TXT, MD, or image files
- Choose document type (IT Policy or HR Policy)
- Wait for processing to complete

### 4. Chat with Documents
- Ask questions in the chat interface
- Examples:
  - "What is the password policy?"
  - "What types of employment categories are mentioned?"
  - "Tell me about data backup procedures"

### 5. View Chat History
- All conversations are saved automatically
- Click on previous chats in the sidebar to view history
- Create new conversations with the "+" button

---

## 🔧 Key Components Explained

### LangGraph Orchestrator (`graph_orchestrator.py`)

The heart of the multi-agent system. It:
1. **Receives queries** and initializes state
2. **Routes to Coordinator** for agent selection
3. **Executes agents in parallel** using LangGraph
4. **Synthesizes responses** from multiple agents
5. **Returns final answer** with source attribution

**Key Features:**
- State management with reducers
- Conditional edges for dynamic routing
- Parallel execution node
- LLM-based synthesis

### Base Agent (`base_agent.py`)

Abstract base class for all specialist agents:
- **Query Processing**: Takes user query and retrieves relevant documents
- **ChromaDB Integration**: Performs semantic search
- **Junk Filtering**: Filters out short chunks at query time (< 100 chars)
- **LLM Response**: Generates answer based on retrieved context
- **Strict Mode**: Only answers from available documents, no hallucinations

### Document Service (`document_service.py`)

Handles all document processing:
- **File Upload**: Saves files to disk and creates MongoDB records
- **Text Extraction**: Extracts text from PDFs, DOCX, and images (OCR)
- **Chunking**: Splits text into overlapping chunks
- **Upload-Time Filtering**: Removes short chunks before embedding
- **Embedding Generation**: Creates vector embeddings with OpenAI
- **ChromaDB Storage**: Stores embeddings with metadata

### Smart Filtering (Two-Layer Approach)

**Why Filtering?**
Documents (especially images with OCR) often contain many short, useless chunks like:
- Page headers/footers
- Page numbers
- Decorative text

These pollute search results, causing the AI to return irrelevant information.

**Solution:**

1. **Upload-Time Filtering** (`document_service.py`):
   - Filters chunks < 100 characters before embedding
   - Saves storage and improves search quality
   - Reduces ChromaDB clutter

2. **Query-Time Filtering** (`base_agent.py`):
   - Retrieves 100 results from ChromaDB
   - Filters out chunks < 100 characters
   - Returns top 5 substantial chunks
   - Handles old documents uploaded before filtering was implemented

---

## 🎨 UI Features

### Design System
- **Color Scheme**: Dark theme with purple (#8B5CF6) accents
- **Typography**: Clean, minimal fonts
- **Glassmorphism**: Subtle transparency with blur effects
- **Animations**: Smooth transitions and animated background orbs

### Responsive Layout
- **Desktop**: Sidebar + main chat area
- **Mobile**: Collapsible sidebar, full-width chat
- **Fixed Elements**: Search bar stays at bottom, headers stay at top
- **Independent Scrolling**: Messages and history scroll separately

---

## 🔒 Security

- **Password Hashing**: bcrypt for secure password storage
- **JWT Tokens**: Stateless authentication
- **Role-Based Access**: Admin-only routes protected
- **Input Validation**: Pydantic models validate all inputs
- **File Upload Validation**: Extension and size restrictions
- **CORS**: Configured for localhost development

---

## 📊 Performance Optimizations

1. **Parallel Agent Execution**: Multiple agents run simultaneously
2. **Batch Embeddings**: Process multiple chunks at once
3. **Vector Search**: Fast semantic similarity with ChromaDB
4. **Runtime Filtering**: Efficient query-time filtering
5. **Connection Pooling**: MongoDB and HTTP connection reuse
6. **Lazy Loading**: Components load on demand

---

## 🐛 Known Issues & Limitations

1. **Python Version**: Must use Python 3.11 or 3.12 (not 3.14)
2. **OCR Performance**: EasyOCR is slower on CPU (faster with GPU)
3. **Image Quality**: OCR accuracy depends on image quality
4. **Context Window**: Limited by LLM token limits (4096 tokens for GPT-4)
5. **ChromaDB Batch Size**: Max 5,461 embeddings per operation

---

## 🔮 Future Enhancements

- [ ] GPU acceleration for OCR
- [ ] Support for more file formats (Excel, PowerPoint)
- [ ] Real-time collaboration
- [ ] Advanced analytics dashboard
- [ ] Export chat transcripts
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Document versioning
- [ ] Automated document summarization

---

## 📝 License

This project is private and proprietary.

---

## 👥 Support

For issues or questions, contact the development team.

---

## 🙏 Acknowledgments

- **LangChain** & **LangGraph** - Agent orchestration framework
- **OpenAI** - LLM and embedding models
- **ChromaDB** - Vector database
- **EasyOCR** - OCR capabilities
- **FastAPI** - Web framework
- **React** - UI framework

---

**Last Updated**: December 2, 2025
