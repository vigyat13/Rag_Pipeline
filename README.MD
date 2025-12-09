<!-- ===================== -->
<!--   GITHUB BANNER       -->
<!-- ===================== -->

<p align="center">
  <img src="https://img.shields.io/badge/ADVANCED-RAG%20SYSTEM-8A2BE2?style=for-the-badge&logo=ai" />
</p>

<h1 align="center">🔍 Advanced RAG Chat System — Multi-Document AI Assistant</h1>

<p align="center">
  <strong>FastAPI • FAISS • Groq LLMs • React • TypeScript • SQLAlchemy</strong>
</p>

---

<details>
<summary><h2>📘 Click to Open Full Project README</h2></summary>

---

# 🚀 Advanced RAG Chat System  
A production-grade **Retrieval-Augmented Generation (RAG)** platform that allows users to upload documents, query them using AI, and monitor analytics — all built using modern AI engineering practices.

---

## ⭐ **Features**

### 📂 Document Intelligence
- Upload PDFs / text files  
- Automatic text extraction (PyMuPDF)  
- Smart document chunking  
- Embedding generation  
- Per-user **FAISS vector index**  
- real-time RAG retrieval  

### 🤖 Multi-Agent AI Chat
Supports 4 powerful modes:
| Mode | What it Does |
|------|--------------|
| **Default** | Direct RAG-grounded answer |
| **Research** | Planner → multi-step reasoning → synthesis |
| **Summarizer** | Structured, concise summaries |
| **Brainstorm** | Generates ideas, suggestions, next steps |

Outputs:
- Answer  
- Source snippets  
- Token usage  
- Latency  

---

## 📊 Analytics Dashboard  
Monitors:
- Total queries  
- Token usage  
- Average latency  
- Query history  
- Document interactions  

Perfect for debugging and evaluating RAG performance.

---

## 🧠 **System Architecture**
              ┌───────────────────────────┐
              │        React Frontend      │
              │  Chat UI • Uploads • Dashboard
              └──────────────┬────────────┘
                             │
                             ▼
                 ┌────────────────────┐
                 │     FastAPI API    │
                 │ Auth • Docs • Chat │
                 └─────────┬──────────┘
                           │
                 ┌─────────▼──────────┐
                 │     RAG Pipeline    │
                 │ Retrieval • Prompt  │
                 │ Multi-agent Logic   │
                 └─────────┬──────────┘
                           │
               ┌──────────▼──────────┐
               │   FAISS Vector DB    │
               │ Per-User Indexes     │
               └──────────┬──────────┘
                           │
               ┌──────────▼──────────┐
               │   SQL Database       │
               │ Users • Docs • Chunks│
               │ Query Analytics      │
               └──────────────────────┘

---

## 🏗️ Tech Stack

### **Backend**
- FastAPI  
- SQLAlchemy ORM  
- FAISS (vector search)  
- PyMuPDF  
- Groq LLM API  
- Pydantic v2  

### **Frontend**
- React 18  
- TypeScript  
- Vite  
- Axios  
- Tailwind UI  

---

## ⚙️ Installation

### 🐍 Backend
```bash
cd advanced-rag-backend
pip install -r requirements.txt
uvicorn app.main:app --reload

cd frontendrag
npm install
npm run dev


