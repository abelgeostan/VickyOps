# VickyOps 🛡️🤖

**Production-Quality AI-Powered DevOps & Server Management Platform**

VickyOps is an AI-powered server management dashboard and DevOps assistant designed for self-hosted Ubuntu servers. It provides visual service management alongside a ChatGPT-style natural-language copilot, both backed by the exact same controlled, security-hardened backend tool layer.

---

## 🌟 Key Architecture & Highlights

- **Dual-Control Core Experience**:
  - **Visual Service Management**: Modern dark-mode cards with real-time Docker container states, Git branches, commit hashes, and actions.
  - **AI DevOps Chat**: A persistent ChatGPT-style assistant capable of understanding questions, formulating multi-step plans, requesting approval for destructive tasks, and executing controlled tools.
  - **Unified Operations**: Clicking an action on the dashboard (such as **"Deploy Update"**) automatically transitions into the activity/chat interface and streams progress step-by-step.
- **Strict Security Architecture**:
  - **NO Arbitrary Shell Access**: The LLM is never given a raw terminal or unconstrained shell.
  - **Controlled Tool Allowlist**: All operations execute through discrete, validated backend tools (`docker.*`, `git.*`, `service.*`, `server.*`, `backup.*`, `cloudflare.*`).
  - **Human-in-the-Loop Approval System**: Dangerous and modifying operations (service restart, stop, git pull, image builds, snapshot restores) pause execution and require explicit user approval.
  - **Immutable Audit Logging**: Every operation, prompt, plan, tool executed, exit code, and duration is permanently recorded in the database.
- **Phase 1 Server Discovery Completed**:
  - Target: Ubuntu Server `vicky` (`192.168.1.123`).
  - Reference Service: **VickyAI** (`/home/stan/VickyAI`), fully configured for Git-based Docker Compose deployments.
  - Other services (StanDrive/stancloud, Nextcloud, n8n, etc.) are cataloged and monitored with custom compatibility guides.

---

## 🏗️ Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, WebSockets.
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2, Paramiko, Passlib/Bcrypt, JWT.
- **Database**: PostgreSQL 16 (with SQLite async fallback for local dev).
- **AI Integration**: Ollama (supports Gemma 3, Qwen 2.5/3, etc. via `OLLAMA_BASE_URL`).
- **Infrastructure**: Docker & Docker Compose.

---

## 🚀 Quick Start

### 1. Run with Docker Compose (Recommended)

```bash
docker compose up -d --build
```

Access the dashboard at:
👉 **`http://localhost:3050`**

### 2. Run in Local Development Mode

#### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 🔧 Controlled Backend Tools

| Tool Name | Risk Level | Description |
| :--- | :--- | :--- |
| `server.get_status` | Safe | Uptime, kernel, OS, hostname, docker daemon state |
| `server.get_resources` | Safe | Real-time CPU%, RAM%, Disk%, Network traffic |
| `docker.list_containers` | Safe | Lists running and stopped Docker workloads |
| `docker.container_status`| Safe | Inspects state, restart count, and container health |
| `docker.logs` | Safe | Tails container stdout/stderr safely |
| `docker.restart` | **Dangerous** | Restarts container (Requires approval) |
| `docker.stop` | **Dangerous** | Stops container (Requires approval) |
| `docker.start` | Safe | Starts stopped container |
| `git.status` | Safe | Checks local branch, commit hash, and working tree |
| `git.check_updates` | Safe | Queries remote git branch via `ls-remote` (no disk writes) |
| `git.pull` | **Dangerous** | Pulls remote branch changes (Requires approval) |
| `service.get_status` | Safe | Multi-container status for compose projects |
| `service.health_check` | Safe | Probes HTTP endpoints or docker healthcheck |
| `service.restart` | **Dangerous** | Restarts compose project (Requires approval) |
| `service.deploy` | **Dangerous** | Standardized 10-step deployment workflow (Requires approval) |
| `backup.create` | Safe | Compressed `.tar.gz` archive of service directories |
| `backup.list` | Safe | Lists stored snapshots |
| `backup.restore` | **Dangerous** | Restores snapshot archive (Requires approval) |
| `cloudflare.get_status`| Safe | Inspects zero-trust tunnel status without secret exposure |

---

## 📦 Deployment Workflow (VickyAI Reference)

1. Verify service directory & `docker-compose.yml`
2. Check Git repository working tree
3. Query GitHub remote for new commits
4. Pull latest `main` branch
5. Build Docker images (`docker compose up -d --build`)
6. Restart and recreate containers
7. Run health checks (`/api/health`)
8. Stream live progress to the user
9. Record audit trail

---

## 🧪 Testing

The backend includes a comprehensive pytest suite verifying tool allowlists, input sanitization, planning logic, and API endpoints:

```bash
pytest backend/tests
```
