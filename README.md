# 💸 Finance-Agent

> A personal-finance chatbot that answers questions about *your* money — grounded in real bank data.

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.142-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-FF6F00)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Postgres + pgvector](https://img.shields.io/badge/Postgres-pgvector-336791?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

**Finance-Agent** is a personal-finance assistant. You import your bank-statements, and can chat with AI agent about your spending, income, savings and plannings in plain language.

Its core principle is **trustworthy numbers**: the LLM never computes a figure. Every total and breakdown comes from your personal data — the model only decides *which* query to run and narrates the result, so it can't hallucinate your balance. And the retrieval layer that grounds the agent's answers on is independently benchmarked.

The project is a compact reference for production-minded LLM engineering: clean agent/tool separation and a RAG pipeline.

---

## Key Features

- 💬 **LangGraph / LangChain chat agent** — a tool-calling agent that answers finance questions with every number grounded in financial guide documents, plus conversation memory.
- 📚 **Evaluated RAG layer** — Tested three pluggable retrieval strategies (dense, hybrid, hybrid + LLM-rerank) benchmarked against a golden set with LLM-as-judge graders in LangSmith.

---

## Tech Stack

| Category | Technologies |
|---|---|
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.0, Pydantic |
| **AI / Agents** | LangChain, LangGraph |
| **RAG / Search** | pgvector (cosine), Postgres full-text, Reciprocal Rank Fusion, LLM reranking |
| **Evaluation** | LangSmith datasets + LLM-as-judge evaluators |
| **Database** | PostgreSQL 16 + `pgvector` |
| **Frontend** | React 19, TypeScript, Vite |
| **Tooling** | `uv`, Docker Compose, Ruff, pytest |
