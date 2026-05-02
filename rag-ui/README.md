# DocRAG UI

React frontend for the PDF RAG service.

## Setup

```bash
npm install
npm start
```

Open http://localhost:3000

## API Configuration

Set your FastAPI backend URL in `.env`:
```
REACT_APP_API_URL=http://localhost:8000
```

## Required: CORS in FastAPI

Add to `main.py` before `app.include_router(...)`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Project Structure

```
src/
├── services/
│   └── api.js           # All API calls (health, upload, ask)
├── hooks/
│   ├── useHealth.js     # Polls /rag/health every 15s
│   ├── useUpload.js     # File state + upload logic with progress
│   └── useChat.js       # Message state + send logic
├── components/
│   ├── DropZone.jsx     # Drag & drop PDF picker
│   ├── FileCard.jsx     # Individual file with status + progress
│   ├── ChatMessage.jsx  # Chat bubble + source chips
│   └── StatusBar.jsx    # Server health indicator
├── App.jsx              # Main layout
└── App.css              # Dark editorial theme
```
