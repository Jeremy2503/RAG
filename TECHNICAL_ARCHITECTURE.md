# Technical Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [LangGraph Implementation](#langgraph-implementation)
3. [Agent Architecture](#agent-architecture)
4. [Data Flow](#data-flow)
5. [Database Design](#database-design)
6. [API Endpoints](#api-endpoints)
7. [Security Architecture](#security-architecture)
8. [Performance Considerations](#performance-considerations)

---

## System Overview

### High-Level Architecture

The system is built on a **microservices-inspired** architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Presentation Layer                          │
│                         (React Frontend)                             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ HTTP/REST
┌─────────────────────────────┴───────────────────────────────────────┐
│                          API Gateway Layer                           │
│                         (FastAPI Routers)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │   Auth   │  │   Chat   │  │Documents │  │   User   │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                         Service Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Auth Service │  │ Chat Service │  │  Doc Service │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   Agent Service                             │    │
│  │  ┌──────────────────────────────────────────────────┐      │    │
│  │  │          LangGraph Orchestrator                  │      │    │
│  │  └──────────────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                         Data Access Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │MongoDB Repo  │  │ Chroma Repo  │  │ Embedding    │             │
│  │              │  │              │  │  Generator   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                         Persistence Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   MongoDB    │  │   ChromaDB   │  │  OpenAI API  │             │
│  │  (Atlas)     │  │   (Local)    │  │ (External)   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## LangGraph Implementation

### State Management

LangGraph uses a typed state object that flows through the workflow:

```python
class AgentState(TypedDict):
    """
    State object that flows through the LangGraph workflow.
    """
    query: str                              # Original user query
    query_history: List[str]                # Previous queries in session
    routing_decision: Dict[str, Any]        # Coordinator's routing decision
    agent_responses: Annotated[             # Agent responses with reducer
        List[Dict[str, Any]], 
        reduce_agent_responses              # Custom reducer function
    ]
    final_response: str                     # Synthesized final answer
    sources: List[Dict[str, Any]]           # Source documents used
    error: Optional[str]                    # Error message if any
```

**Key Concept - Annotated with Reducer:**
```python
def reduce_agent_responses(
    existing: List[Dict[str, Any]], 
    new: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Reducer function that combines agent responses.
    Prevents duplicates and maintains order.
    """
    return existing + new
```

### Graph Structure

```python
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("coordinator", self._coordinator_node)
workflow.add_node("parallel_agent_executor", self._parallel_agent_executor)
workflow.add_node("research_agent", self._research_node)
workflow.add_node("it_policy_agent", self._it_policy_node)
workflow.add_node("hr_policy_agent", self._hr_policy_node)
workflow.add_node("synthesize", self._synthesize_node)

# Define entry point
workflow.set_entry_point("coordinator")

# Add conditional routing
workflow.add_conditional_edges(
    "coordinator",
    self._route_after_coordinator,
    {
        "parallel": "parallel_agent_executor",
        "research_only": "research_agent",
        "end": END
    }
)

# Converge to synthesis
workflow.add_edge("parallel_agent_executor", "synthesize")
workflow.add_edge("research_agent", "synthesize")
workflow.add_edge("synthesize", END)
```

### Node Implementations

#### 1. Coordinator Node
```python
def _coordinator_node(self, state: AgentState) -> AgentState:
    """
    Analyzes query and determines which agents should handle it.
    
    Returns:
        Updated state with routing_decision
    """
    result = self.coordinator.process(
        query=state["query"],
        query_history=state.get("query_history", [])
    )
    
    return {
        "routing_decision": {
            "agents": result["agents"],
            "reasoning": result["reasoning"],
            "confidence": result["confidence"]
        }
    }
```

#### 2. Parallel Agent Executor
```python
def _parallel_agent_executor(self, state: AgentState) -> AgentState:
    """
    Executes multiple agents in parallel using asyncio.
    
    Returns:
        Updated state with agent_responses (appended via reducer)
    """
    agents_to_invoke = state["routing_decision"]["agents"]
    
    # Execute agents in parallel
    results = await asyncio.gather(*[
        self._execute_agent(agent_name, state["query"])
        for agent_name in agents_to_invoke
    ])
    
    return {
        "agent_responses": results  # Reducer combines with existing
    }
```

#### 3. Synthesis Node
```python
def _synthesize_node(self, state: AgentState) -> AgentState:
    """
    Combines multiple agent responses into a coherent answer.
    Uses LLM to intelligently merge information.
    
    Returns:
        Updated state with final_response and sources
    """
    responses = state["agent_responses"]
    
    # Build synthesis prompt
    synthesis_prompt = self._build_synthesis_prompt(
        query=state["query"],
        responses=responses
    )
    
    # Generate final answer
    final_answer = await self.llm.agenerate(synthesis_prompt)
    
    # Collect all sources
    sources = self._collect_sources(responses)
    
    return {
        "final_response": final_answer,
        "sources": sources
    }
```

### Conditional Routing Logic

```python
def _route_after_coordinator(self, state: AgentState) -> str:
    """
    Determines next step based on coordinator's decision.
    """
    agents = state["routing_decision"]["agents"]
    
    if not agents or agents == []:
        return "end"  # No agents needed
    
    if len(agents) == 1 and agents[0] == "research":
        return "research_only"  # Direct to research
    
    return "parallel"  # Execute multiple agents in parallel
```

---

## Agent Architecture

### Base Agent Class

All specialist agents inherit from `BaseAgent`:

```python
class BaseAgent(ABC):
    """
    Abstract base class for all specialist agents.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        llm,
        chroma_repo: ChromaRepository,
        embedding_generator
    ):
        self.name = name
        self.description = description
        self.llm = llm
        self.chroma_repo = chroma_repo
        self.embedding_generator = embedding_generator
    
    async def process(
        self, 
        query: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main processing method - must be implemented by subclasses.
        """
        # 1. Retrieve relevant documents
        documents = await self._retrieve_documents(query, **kwargs)
        
        # 2. Generate response using LLM
        response = await self._generate_response(query, documents)
        
        # 3. Return structured result
        return {
            "agent": self.name,
            "response": response,
            "sources": documents,
            "metadata": {}
        }
    
    async def _retrieve_documents(
        self, 
        query: str, 
        document_type: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant documents with smart filtering.
        """
        # Generate query embedding
        query_embedding = await self.embedding_generator.generate_embeddings([query])
        
        # Query ChromaDB (get extra for filtering)
        results = self.chroma_repo.query_by_text(
            query_text=query,
            query_embedding=query_embedding,
            n_results=n_results * 20,  # Get 20x for filtering
            document_type=document_type
        )
        
        # Filter out short chunks (junk)
        MIN_CHUNK_LENGTH = 100
        filtered_results = [
            doc for doc in results 
            if len(doc.get('content', '').strip()) >= MIN_CHUNK_LENGTH
        ]
        
        # Return top N after filtering
        return filtered_results[:n_results]
    
    @abstractmethod
    async def _get_system_prompt(self) -> str:
        """
        Returns agent-specific system prompt.
        """
        pass
```

### Specialist Agent Implementation

```python
class HRPolicyAgent(BaseAgent):
    """
    Specialist agent for HR policy queries.
    """
    
    def __init__(self, llm, chroma_repo, embedding_generator):
        super().__init__(
            name="HR Policy Agent",
            description="Expert in HR policies, benefits, leave, compensation",
            llm=llm,
            chroma_repo=chroma_repo,
            embedding_generator=embedding_generator
        )
    
    async def _get_system_prompt(self) -> str:
        return """
        You are an HR Policy Agent, an expert in human resources.
        
        CRITICAL INSTRUCTIONS:
        1. Answer ONLY using the exact information from the provided context
        2. Do NOT add interpretations or infer information
        3. If the context contains the answer, provide it as written
        4. If the context does NOT contain the answer, state:
           "This information is not found in the available HR policy documents."
        5. Be conversational but factually strict
        """
    
    async def process(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Process HR policy query with domain-specific filtering.
        """
        # Retrieve HR policy documents only
        documents = await self._retrieve_documents(
            query=query,
            document_type="hr_policy",  # Domain-specific filter
            n_results=5
        )
        
        # Generate response
        response = await self._generate_response(query, documents)
        
        return {
            "agent": self.name,
            "response": response,
            "sources": documents,
            "metadata": {
                "document_type": "hr_policy",
                "num_sources": len(documents)
            }
        }
```

---

## Data Flow

### Document Upload Flow

```
User uploads file
    │
    ▼
┌─────────────────────────┐
│  1. API Endpoint        │
│  POST /documents/upload │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  2. Document Service    │
│  - Save file to disk    │
│  - Create DB record     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  3. Text Extraction     │
│  - PDF: PyPDF2          │
│  - DOCX: python-docx    │
│  - Image: EasyOCR       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  4. Chunking            │
│  - Split into 500 chars │
│  - 50 char overlap      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  5. Upload Filtering    │
│  - Remove chunks < 100  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  6. Embedding Gen       │
│  - OpenAI API call      │
│  - text-embedding-3     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  7. ChromaDB Storage    │
│  - Store embeddings     │
│  - Store metadata       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  8. Update DB Record    │
│  - Status: completed    │
│  - Chunk count          │
└─────────────────────────┘
```

### Query Processing Flow

```
User sends query
    │
    ▼
┌─────────────────────────┐
│  1. API Endpoint        │
│  POST /chat/query       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  2. Chat Service        │
│  - Add to history       │
│  - Forward to agents    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  3. LangGraph           │
│  - Coordinator          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  4. Parallel Execution  │
│  ┌────┐ ┌────┐ ┌────┐  │
│  │ IT │ │ HR │ │Res.│  │
│  └────┘ └────┘ └────┘  │
└───────────┬─────────────┘
            │
            ├─ Each agent:
            │  1. Generate embedding
            │  2. Query ChromaDB
            │  3. Filter results
            │  4. Generate response
            │
            ▼
┌─────────────────────────┐
│  5. Synthesis           │
│  - Combine responses    │
│  - Deduplicate sources  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  6. Save to History     │
│  - MongoDB              │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  7. Return to Frontend  │
│  - Response + sources   │
└─────────────────────────┘
```

---

## Database Design

### MongoDB Collections

#### 1. Users Collection
```javascript
{
  "_id": ObjectId("..."),
  "email": "user@example.com",
  "full_name": "John Doe",
  "hashed_password": "$2b$12$...",
  "role": "user",  // or "admin"
  "is_active": true,
  "created_at": ISODate("..."),
  "updated_at": ISODate("..."),
  "last_login": ISODate("...")
}
```

#### 2. Documents Collection
```javascript
{
  "_id": ObjectId("..."),
  "filename": "uuid_original-name.pdf",
  "original_filename": "original-name.pdf",
  "file_path": "data/uploads/uuid_original-name.pdf",
  "file_size": 1024000,
  "file_type": "application/pdf",
  "document_type": "hr_policy",  // or "it_policy", "research"
  "uploaded_by": ObjectId("..."),  // User ID
  "uploaded_at": ISODate("..."),
  "updated_at": ISODate("..."),
  "status": "completed",  // or "pending", "processing", "failed"
  "chunks_count": 42,
  "embeddings_stored": true,
  "chroma_collection": "policy_documents",
  "processing_started_at": ISODate("..."),
  "processing_completed_at": ISODate("...")
}
```

#### 3. Chat History Collection
```javascript
{
  "_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "title": "Tell me about password policy",
  "messages": [
    {
      "id": "uuid-1",
      "role": "user",
      "content": "Tell me about password policy",
      "timestamp": ISODate("...")
    },
    {
      "id": "uuid-2",
      "role": "assistant",
      "content": "The password policy requires...",
      "timestamp": ISODate("..."),
      "agent_type": "it_policy",
      "metadata": {
        "routing_decision": {...},
        "sources": [...]
      }
    }
  ],
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

### ChromaDB Schema

```python
# Collection: policy_documents
{
    "ids": ["chunk_doc-id_0", "chunk_doc-id_1", ...],
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],  # 1536-dim vectors
    "documents": ["chunk text 1", "chunk text 2", ...],
    "metadatas": [
        {
            "document_id": "mongodb_doc_id",
            "filename": "original-name.pdf",
            "document_type": "hr_policy",
            "chunk_id": 0,
            "chunk_size": 500,
            "uploaded_by": "user_id",
            "uploaded_at": "2025-12-02T10:00:00Z"
        },
        ...
    ]
}
```

---

## API Endpoints

### Authentication

```
POST   /api/v1/auth/register         Register new user
POST   /api/v1/auth/login            User login
POST   /api/v1/auth/admin/login      Admin login
GET    /api/v1/auth/me               Get current user
```

### Documents

```
POST   /api/v1/documents/upload      Upload document
GET    /api/v1/documents             List user's documents
GET    /api/v1/documents/{id}        Get document details
DELETE /api/v1/documents/{id}        Delete document (admin only)
```

### Chat

```
POST   /api/v1/chat/sessions         Create new chat session
GET    /api/v1/chat/sessions         List user's sessions
GET    /api/v1/chat/sessions/{id}    Get session details
POST   /api/v1/chat/query            Send query to agents
DELETE /api/v1/chat/sessions/{id}    Delete session
```

---

## Security Architecture

### Authentication Flow

```
1. User submits credentials
     │
     ▼
2. Backend validates
     │
     ├─ Valid: Generate JWT token
     │   {
     │     "sub": "user_id",
     │     "email": "user@example.com",
     │     "role": "user",
     │     "exp": timestamp
     │   }
     │
     └─ Invalid: Return 401
     
3. Frontend stores token in localStorage

4. All subsequent requests include:
   Authorization: Bearer <token>

5. Backend validates token on each request
     │
     ├─ Valid: Process request
     └─ Invalid/Expired: Return 401
```

### Role-Based Access Control

```python
def require_admin(token: str = Depends(oauth2_scheme)):
    """
    Decorator for admin-only endpoints.
    """
    user = verify_token(token)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

---

## Performance Considerations

### 1. Parallel Agent Execution

**Before (Sequential):**
```
IT Agent (2s) → HR Agent (2s) → Research Agent (2s) = 6s total
```

**After (Parallel):**
```
┌─ IT Agent (2s) ──┐
├─ HR Agent (2s) ──┤  = 2s total
└─ Research (2s) ──┘
```

### 2. Batch Embedding Generation

```python
# Instead of:
for text in texts:
    embedding = await generate_embedding(text)  # N API calls

# Do this:
embeddings = await generate_embeddings(texts)  # 1 API call
```

### 3. ChromaDB Query Optimization

```python
# Query with filtering reduces search space
results = collection.query(
    query_embeddings=embedding,
    n_results=100,
    where={"document_type": "hr_policy"}  # Pre-filter
)
```

### 4. Two-Layer Filtering Strategy

- **Upload-Time**: Filter before embedding (saves API costs)
- **Query-Time**: Filter after retrieval (handles legacy data)

### 5. Connection Pooling

```python
# MongoDB
client = MongoClient(
    MONGODB_URI,
    maxPoolSize=50,  # Connection pool
    minPoolSize=10
)

# HTTP
httpx_client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20)
)
```

---

## Monitoring & Debugging

### Logging Strategy

```python
# app/main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Key loggers:
# - app.agents.* → Agent processing
# - app.repositories.* → Database operations
# - app.services.* → Business logic
# - openai.* → API calls
```

### Key Metrics to Track

1. **Query Latency**: Time from query to response
2. **Agent Execution Time**: Individual agent performance
3. **ChromaDB Query Time**: Vector search performance
4. **OpenAI API Latency**: LLM and embedding generation time
5. **Document Processing Time**: Upload to completion
6. **Error Rates**: Failed queries, uploads, authentication

---

## Deployment Considerations

### Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...
MONGODB_URI=mongodb+srv://...
SECRET_KEY=random-secret-key-here

# Optional (with defaults)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_EXTENSIONS=.pdf,.docx,.txt,.md,.jpg,.jpeg,.png
MAX_FILE_SIZE=10485760
CHROMA_PERSIST_DIRECTORY=./data/chroma
```

### Production Checklist

- [ ] Set secure `SECRET_KEY`
- [ ] Use MongoDB Atlas (not local)
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable request logging
- [ ] Set up error monitoring (Sentry)
- [ ] Configure backup strategy
- [ ] Set resource limits (memory, CPU)
- [ ] Enable GPU for EasyOCR if available

---

**Document Version**: 1.0  
**Last Updated**: December 2, 2025


