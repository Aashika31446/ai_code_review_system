# AI-Assisted Code Review System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18%2B-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

An enterprise-grade, automated code inspection platform combining deterministic static analysis (AST parsing, linter metrics, security scans) with intelligent Large Language Model reasoning (Google Gemini & OpenAI GPT). The system provides developers with real-time feedback, actionable inline refactoring suggestions, security vulnerability detection, and automated architectural reviews.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Local Development (Without Docker)](#local-development-without-docker)
  - [1. Database Setup](#1-database-setup)
  - [2. Backend Service](#2-backend-service)
  - [3. Code Analyzer Module](#3-code-analyzer-module)
  - [4. AI Engine Module](#4-ai-engine-module)
  - [5. Frontend Application](#5-frontend-application)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Team Members & Module Ownership](#team-members--module-ownership)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Static Code Analysis**: Syntactic complexity metrics (Cyclomatic complexity, maintainability index), static AST inspection, and integrated Ruff and Bandit scanners.
- **AI-Powered Code Review**: Context-aware review generation via Google Gemini 1.5 or OpenAI GPT-4, pinpointing anti-patterns, edge cases, and architectural smells.
- **Security & Vulnerability Detection**: Identifies OWASP Top 10 security flaws, hardcoded credentials, insecure dependencies, and injection vectors.
- **Interactive Web Dashboard**: Modern React interface featuring side-by-side diff viewers, severity filtering (Critical, High, Medium, Low), and review history.
- **JWT Authentication & RBAC**: Secure user registration, OAuth2 password bearer authentication, and isolated tenant project workspaces.
- **Repository & Archive Ingestion**: Supports uploading project ZIP archives, individual files, or connecting remote repository sources.
- **Production CI/CD Automation**: GitHub Actions pipeline for continuous testing, dependency validation, and multi-service Docker Compose orchestration.

---

## Architecture

```
+---------------------------------------------------------------------------------------+
|                                    CLIENT BROWSER                                     |
|                              (React 18 / Vite / Tailwind)                             |
|                                 http://localhost:3000                                 |
+------------------------------------------+--------------------------------------------+
                                           |
                                  HTTP / REST API Calls
                                  (Bearer JWT Auth)
                                           v
+---------------------------------------------------------------------------------------+
|                                  BACKEND API GATEWAY                                  |
|                             (FastAPI ASGI Server / Uvicorn)                           |
|                                 http://localhost:8000                                 |
+-------------------+-----------------------------------------------+-------------------+
                    |                                               |
                    v                                               v
+-------------------------------------+           +-------------------------------------+
|        STATIC CODE ANALYZER         |           |              AI ENGINE              |
|        (`code-analyzer/`)           |           |             (`ai-engine/`)          |
|  - AST Traversal & Tokenizer        |           |  - Prompt Engineering & Context     |
|  - Cyclomatic & Halstead Metrics    |           |  - Google Gemini 1.5 Pro / Flash    |
|  - Bandit Security Scanner          |           |  - OpenAI GPT-4o / Assistant API    |
|  - Ruff Linter Orchestration        |           |  - Structured JSON Output Validator |
+-------------------+-----------------+           +-----------------+-------------------+
                    |                                               |
                    +-----------------------+-----------------------+
                                            | Aggregated Review Results
                                            v
+---------------------------------------------------------------------------------------+
|                               PERSISTENCE & STORAGE                                   |
|  +------------------------------------+   +----------------------------------------+  |
|  |     PostgreSQL 15 Database         |   |         Persistent Uploads Volume      |  |
|  |  - Users, Projects, Reviews, Logs  |   |  - Extracted code archives & artifacts |  |
|  +------------------------------------+   +----------------------------------------+  |
+---------------------------------------------------------------------------------------+
```

---

## Tech Stack

| Domain | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide Icons | Responsive UI with real-time feedback & code diff viewer |
| **Backend** | Python 3.11, FastAPI, Uvicorn, Pydantic v2 | High-performance asynchronous REST API framework |
| **Database** | PostgreSQL 15, SQLAlchemy 2.0, Alembic | Relational storage for user entities, projects, and review logs |
| **AI Integration** | Google Generative AI (Gemini), OpenAI API | LLM engines generating contextual code suggestions |
| **Code Analysis** | AST, Ruff, Bandit, Radon | Static code inspection, security audits, and complexity scoring |
| **Authentication** | OAuth2, JWT (python-jose), Passlib (bcrypt) | Secure stateless token-based authorization |
| **DevOps & Containers** | Docker, Docker Compose, GitHub Actions | Multi-container environment and automated CI/CD pipeline |

---

## Prerequisites

Before setting up the project, ensure you have the following installed on your host machine:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24.0+ recommended) with Docker Compose v2.20+
- [Node.js](https://nodejs.org/) (v20 LTS recommended) and `npm` (v10+)
- [Python](https://www.python.org/downloads/) (v3.11+) and `pip`
- [PostgreSQL](https://www.postgresql.org/) (v15+) *(only required if running natively without Docker)*
- [Git](https://git-scm.com/)

---

## Quick Start with Docker

Get the entire stack (Database, Backend, Frontend, and Volumes) up and running in 5 simple steps:

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-org/ai-code-review-system.git
cd ai-code-review-system
```

### Step 2: Create Environment Configuration
Copy the sample environment file to initialize your local `.env`:
```bash
cp .env.example .env
```

### Step 3: Configure Your AI Provider API Key
Open `.env` in your preferred editor and provide at least one valid API key:
```env
# Choose 'gemini' or 'openai'
AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyYourActualGeminiApiKeyHere
# Or configure OpenAI
OPENAI_API_KEY=sk-proj-YourActualOpenAIApiKeyHere
```

### Step 4: Launch the Container Stack
Start PostgreSQL, Backend, and Frontend containers in detached mode:
```bash
docker compose up --build -d
```
Check running containers:
```bash
docker compose ps
```

### Step 5: Open in Your Browser
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Backend Interactive API (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

To view streaming container logs:
```bash
docker compose logs -f
```

To stop all containers:
```bash
docker compose down
```

---

## Local Development (Without Docker)

Follow these instructions to run the application components locally on your host system.

### 1. Database Setup
Ensure PostgreSQL 15 is running locally:
```sql
CREATE USER postgres WITH PASSWORD 'password';
CREATE DATABASE code_review_db OWNER postgres;
```

### 2. Backend Service
1. Navigate to the backend directory and create a virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   ```
2. Activate the virtual environment:
   - **Linux / macOS**:
     ```bash
     source .venv/bin/activate
     ```
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
3. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Set the Python path to include sibling engines:
   - **Linux / macOS**:
     ```bash
     export PYTHONPATH=.:../code-analyzer:../ai-engine
     ```
   - **Windows (PowerShell)**:
     ```powershell
     $env:PYTHONPATH=".;..\code-analyzer;..\ai-engine"
     ```
5. Launch the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 3. Code Analyzer Module
The static code analyzer can be developed and verified independently:
```bash
cd code-analyzer
pytest tests/ -v
```

### 4. AI Engine Module
The AI engine encapsulates prompts and API connectors:
```bash
cd ai-engine
pytest tests/ -v
```

### 5. Frontend Application
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev -- --host 0.0.0.0 --port 3000
   ```
4. Access the web client at [http://localhost:3000](http://localhost:3000).

---

## API Documentation

FastAPI automatically generates interactive, OpenAPI-compliant documentation:

- **Swagger UI**: Accessible at [http://localhost:8000/docs](http://localhost:8000/docs). Allows real-time endpoint execution, request payload modeling, and JWT token authorization testing.
- **ReDoc UI**: Accessible at [http://localhost:8000/redoc](http://localhost:8000/redoc) for comprehensive schema exploration.

### Primary API Endpoints Overview

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | System health check and uptime probe |
| `POST` | `/api/auth/register` | Public | Register a new developer account |
| `POST` | `/api/auth/login` | Public | Authenticate credentials and receive Bearer JWT |
| `GET` | `/api/projects` | Authenticated | Retrieve list of registered projects |
| `POST` | `/api/projects` | Authenticated | Create a new code project workspace |
| `POST` | `/api/projects/{id}/upload` | Authenticated | Upload ZIP archive or code files for review |
| `POST` | `/api/reviews/trigger` | Authenticated | Execute combined static analysis & AI review |
| `GET` | `/api/reviews/{id}` | Authenticated | Retrieve detailed review report and diagnostics |

---

## Project Structure

```text
ai-code-review-system/
│
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI workflow (tests, builds, lints)
│
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git ignore patterns for Python, Node, Docker
├── docker-compose.yml           # Multi-container orchestration (db, backend, frontend)
├── README.md                    # Project documentation
│
├── backend/
│   ├── Dockerfile               # Backend container definition (Python 3.11 slim)
│   ├── requirements.txt         # Production & development dependencies
│   └── app/
│       ├── __init__.py
│       ├── main.py              # FastAPI application entrypoint & middleware
│       ├── api/                 # API routers (auth, projects, reviews)
│       ├── core/                # JWT tokens, security, config settings
│       ├── db/                  # SQLAlchemy models and session management
│       └── services/            # Review orchestrator & file management
│
├── frontend/
│   ├── Dockerfile               # Frontend container definition (Node 20 Alpine)
│   ├── package.json             # React dependencies and scripts
│   ├── vite.config.js           # Vite development server configuration
│   ├── index.html               # Single page application root HTML
│   └── src/
│       ├── components/          # UI components (DiffViewer, MetricsCard, Navbar)
│       ├── pages/               # Dashboard, Login, ProjectDetails
│       └── services/            # Axios API client bindings
│
├── code-analyzer/               # Static analysis engine
│   ├── __init__.py
│   ├── ast_parser.py            # AST visitor for syntax and structural metrics
│   ├── complexity.py            # Cyclomatic & Halstead scoring
│   └── security_scanner.py      # Bandit & pattern rule execution
│
├── ai-engine/                   # AI Reviewer engine
│   ├── __init__.py
│   ├── gemini_client.py         # Google Gemini 1.5 Pro integration
│   ├── openai_client.py         # OpenAI GPT-4o integration
│   ├── prompt_templates.py      # Targeted code review prompts
│   └── parser.py                # Structured response parser & validator
│
├── tests/                       # Automated test suites
│   ├── __init__.py
│   └── test_backend.py          # Pytest suite for health, auth, and projects
│
└── uploads/                     # Local file upload directory (git-ignored)
```

---

## Environment Variables

The table below describes all available configuration variables supported in `.env`:

| Variable | Required | Default Value | Description |
| :--- | :---: | :--- | :--- |
| `DATABASE_URL` | **Yes** | `postgresql://postgres:password@db:5432/code_review_db` | PostgreSQL connection string |
| `POSTGRES_USER` | **Yes** | `postgres` | Superuser username for PostgreSQL container |
| `POSTGRES_PASSWORD` | **Yes** | `password` | Superuser password for PostgreSQL container |
| `POSTGRES_DB` | **Yes** | `code_review_db` | Target PostgreSQL database name |
| `SECRET_KEY` | **Yes** | *(random string)* | Cryptographic key used to sign JWT tokens |
| `ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT expiration duration in minutes |
| `AI_PROVIDER` | **Yes** | `gemini` | Target AI provider (`gemini` or `openai`) |
| `GEMINI_API_KEY` | Optional | *(empty)* | Google Gemini API key (required if `AI_PROVIDER=gemini`) |
| `OPENAI_API_KEY` | Optional | *(empty)* | OpenAI API key (required if `AI_PROVIDER=openai`) |
| `UPLOAD_DIR` | No | `./uploads` | Directory for uploaded source archives |
| `MAX_FILE_SIZE_MB` | No | `50` | Maximum allowable file upload size (MB) |
| `VITE_API_BASE_URL` | **Yes** | `http://localhost:8000/api` | Backend API base URL accessible by frontend |

---

## Team Members & Module Ownership

| Name / Role | Assigned Module | Responsibilities & Scope | Primary Technologies |
| :--- | :--- | :--- | :--- |
| **DevOps Engineer** | DevOps & Infrastructure | Docker Compose, CI/CD Actions, environment configs, tests | Docker, GitHub Actions, Pytest |
| **Backend Engineer** | Backend API Gateway | REST API routing, PostgreSQL schemas, JWT auth, uploads | FastAPI, SQLAlchemy, PostgreSQL |
| **Static Analysis Lead**| Code Analyzer Engine | AST analysis, complexity calculation, Bandit & Ruff scans | Python `ast`, Ruff, Bandit, Radon |
| **AI Systems Lead** | AI Review Engine | Gemini & OpenAI connectors, prompt engineering, parsers | Google GenAI SDK, OpenAI API |
| **Frontend Engineer** | Web Dashboard | Responsive UI, code diff visualization, review explorer | React, Vite, Tailwind CSS |

---

## Testing & Quality Assurance

### Running Backend Tests
Execute pytest across the test directory:
```bash
pytest tests/ -v
```

### Running Code Quality & Linting
Run Ruff against all Python modules:
```bash
ruff check backend/ code-analyzer/ ai-engine/
```
To automatically apply safe fixes:
```bash
ruff check --fix backend/ code-analyzer/ ai-engine/
```

### Running Security Audits
Perform static security vulnerability scanning with Bandit:
```bash
bandit -r backend/ code-analyzer/ ai-engine/
```

### Testing Frontend Build
Verify that the React production bundle compiles cleanly:
```bash
cd frontend
npm run build
```

---

## Contributing

1. **Fork the Repository** and create your branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
2. **Commit Your Changes**:
   ```bash
   git commit -m "feat(analyzer): add AST cyclomatic complexity calculation"
   ```
3. **Verify Linting & Tests**:
   Ensure all tests pass and Ruff checks report 0 errors before pushing.
4. **Push to Your Branch**:
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**: Submit your PR targeting the `main` branch.

---
