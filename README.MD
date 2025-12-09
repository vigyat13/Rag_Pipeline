🚀 Advanced RAG Chat System (Multi-Document AI Assistant)

A production-grade Retrieval-Augmented Generation (RAG) system that lets users upload documents, chat with AI over their content, and view detailed usage analytics.
Built end-to-end with FastAPI, FAISS, Groq LLMs, React, and TypeScript.

⭐ Key Features
📂 Smart Document Processing

Upload PDFs and text files

Automatic text extraction, chunking, embeddings

Per-user FAISS vector index for fast retrieval

🤖 AI-Powered RAG Chat

Supports multiple agent modes:

Default → direct answer from retrieved context

Research Mode → planner agent + multi-step synthesis

Summarizer → structured summaries

Brainstorm → creative idea generation

Returns:

Answer

Relevant document snippets

Token usage

Latency metrics

📊 Built-in Analytics Dashboard

Total queries

Token consumption

Average latency

Full query history with modes & documents used

🏗️ Tech Stack
Backend

FastAPI

SQLAlchemy

SQLite/Postgres

FAISS

PyMuPDF (text extraction)

Groq LLM API (Llama models)

Frontend

React + TypeScript

Vite

Axios

Tailwind UI components

🧠 Architecture Overview
User → React Frontend → FastAPI Backend → RAG Pipeline → Groq LLM
           ↑                   ↓
      Analytics Page ← Query Analytics DB

🚀 How It Works

User uploads a document
→ Extract text → Chunk → Embed → Store in FAISS + DB

User asks a question
→ Embed query → Retrieve top-K chunks → Build prompt → LLM answers

System logs analytics
→ latency, tokens, mode, docs used

flowchart LR
    subgraph Frontend (React / Vite)
        U[User Browser]
        D[Documents Page]
        C[Chat Page]
        A[Analytics Page]
    end

    subgraph Backend (FastAPI)
        Auth[Auth Router /api/auth/*]
        Docs[Documents Router /api/documents/*]
        Chat[Chat Router /api/chat/query]
        An[Analytics Router /api/analytics/*]

        subgraph Services
            Chunk[PDF Text Extract + Chunker]
            Emb[Embeddings Service]
            Faiss[FAISS Index]
            RAG[rag_pipeline.py]
            Agents[agents.py]
            AnalyticsSvc[analytics.py]
        end

        subgraph DB (SQLite / Postgres)
            Users[(users)]
            Documents[(documents)]
            Chunks[(document_chunks)]
            QAnalytics[(query_analytics)]
        end
    end

    U --> D --> Docs
    U --> C --> Chat
    U --> A --> An

    Docs --> Chunk --> Emb --> Faiss
    Chunk --> Chunks
    Docs --> Documents

    Chat --> RAG --> Faiss
    RAG --> Agents
    RAG --> AnalyticsSvc --> QAnalytics
    Auth --> Users

📸 UI Screens

Documents page | Chat interface | Analytics dashboard
(Include screenshots here for recruiters)

📦 Run Locally
# Backend
cd advanced-rag-backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontendrag
npm install
npm run dev

🧑‍💻 About the Developer

This project demonstrates skills in LLM engineering, backend architecture, vector search, MLOps principles, and full-stack UI development—built for real-world AI product workflows.
