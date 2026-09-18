# 🏛️ Apex Venture Partners — Autonomous AI Venture Studio

> **Institutional Venture Validation, Quantitative Financial Modeling & Due Diligence Platform**  
> Powered by Multi-Agent AI, Adversarial Stress Testing, and Local LLM Reasoning (`gemma4:12b` via Ollama).

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Vite + React](https://img.shields.io/badge/frontend-Vite%20%2B%20React-646CFF.svg)](https://vitejs.dev/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/local%20LLM-gemma4%3A12b-black.svg)](https://ollama.com/)

---

## ⚡ Quickstart: Run Directly from GitHub

You can run this project in **two ways**:
1. **[Directly in Your Browser (GitHub Codespaces)](#method-1-run-directly-in-browser-github-codespaces)** — Zero local installation required.
2. **[Locally on Your Machine (macOS / Linux / Windows)](#method-2-run-locally-on-your-machine)** — Full local hardware acceleration with Ollama.

---

### Method 1: Run Directly in Browser (GitHub Codespaces)

1. On the GitHub repository page, click the green **`<> Code`** button.
2. Switch to the **Codespaces** tab and click **`Create codespace on main`**.
3. Once the Codespace terminal loads, run:
   ```bash
   # 1. Start the Backend
   cd backend
   pip install -r requirements.txt
   python main.py &

   # 2. Start the Frontend
   cd ../frontend
   npm install
   npm run dev -- --host
   ```
4. A popup will appear: *"Your application running on port 5173 is available."* Click **Open in Browser** to launch the dashboard!

---

### Method 2: Run Locally on Your Machine

#### Prerequisites
* **Git** installed ([Download Git](https://git-scm.com/))
* **Python 3.10+** installed ([Download Python](https://www.python.org/))
* **Node.js 18+** installed ([Download Node.js](https://nodejs.org/))
* **Ollama** installed ([Download Ollama](https://ollama.com/))

---

#### Step 1: Clone the Repository
```bash
git clone https://github.com/saifpimpare6786-dotcom/ai-venture-studio.git
cd ai-venture-studio
```

---

#### Step 2: Set Up & Pull the LLM (Ollama)
Ensure Ollama is running and pull the `gemma4:12b` model:
```bash
# Start Ollama service (if not already running as a background service)
ollama serve

# In a new terminal, pull the recommended model:
ollama pull gemma4:12b
```
*(Note: If you have hardware constraints, you can also pull smaller models like `ollama pull qwen2.5:7b` or `ollama pull llama3.2:3b`).*

---

#### Step 3: Start the Backend Server (FastAPI)
Open a terminal in the project root:
```bash
cd backend

# (Optional but recommended) Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start the server
python main.py
```
> The backend server will start at `http://localhost:8000`  
> Interactive API Docs (Swagger UI): `http://localhost:8000/docs`

---

#### Step 4: Start the Frontend Application (Vite + React)
Open a **second terminal** in the project root:
```bash
cd frontend

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```
> The dashboard will launch at: **`http://localhost:5173`**

---

## 🏛️ Core Platform Features

### 1. Autonomous 13-Deliverable Due Diligence Suite
Generates mathematically coherent, investment-grade memorandums in < 120 seconds:
- **§1.0 Executive Summary** — Core concept, market sizing triangulation, unit economics thesis.
- **§2.0 Business Model Canvas** — 9-block Osterwalder institutional mapping.
- **§3.0 Full Business Plan** — Operational, regulatory, and hiring milestones.
- **§4.0 SWOT Analysis** — Defensibility moats and risk mitigation frameworks.
- **§5.0 PESTLE Analysis** — Macro jurisdictional and economic risk factors.
- **§6.0 Competitor Analysis Matrix** — 2x2 Positioning Quadrant and whitespace moats.
- **§7.0 Porter's Five Forces** — Supplier, buyer, and substitution pricing gravity.
- **§8.0 Marketing & GTM Plan** — B2B incubator wedges, PLG virality loops, and CAC payback.
- **§9.0 Financial Projections** — 36-month statement of operations, cash burn, and breakeven.
- **§10.0 Investment Readiness Memo** — Composite scoring, MOIC & IRR returns triangulation.
- **§11.0 Risk Assessment Matrix** — 2D Severity Heatmap (ISO 31000) across 4 pillars.
- **§12.0 ESG & Sustainability** — Green AI hyperscaler cloud benchmarks, PUE, and carbon targets.
- **§13.0 16:9 Pitch Deck** — 11 presentation slides with DALL-E/Midjourney prompts and speaker notes.

### 2. Interactive Advisory & Deal Tools
- **VC Partner Interrogation Cockpit (🎙️)**: Live interactive partner grilling session with 3 distinct VC personas (*Marcus Vance*, *Dr. Aris Thorne*, *Eleanor Sterling*).
- **"What Must Be True" Inversion Calculator**: Reverse-engineers target enterprise valuation into mandatory operating hurdles (ending ARR, active logos, churn ceiling, required NRR).
- **ARR Bridge Waterfall Chart**: Visual Goldman Sachs-style breakdown of ARR evolution ($Starting + New + Expansion - Churn = Ending$).
- **Multi-Format Export Engine**: 1-click downloads for **Word Memo (`.docx`)**, **16:9 Pitch Deck (`.pptx`)**, **Advisory PDF (`.pdf`)**, and **4-Sheet Financial Model (`.xlsx`)**.

---

## 📁 Repository Architecture

```
ai-venture-studio/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routes (reports, projects, simulator, stream)
│   │   ├── core/            # Configuration & JWT authentication
│   │   ├── database/        # SQLite async persistence (venture_studio.db)
│   │   ├── pipeline/        # Multi-agent LangGraph orchestrator & report synthesis
│   │   └── schemas/         # Pydantic data contracts
│   ├── services/
│   │   ├── excel_financial_generator.py  # 4-sheet financial model engine
│   │   ├── export_generator.py           # DOCX, PPTX, PDF, and XLSX builder
│   │   ├── llm.py                       # Local Ollama + Cloud LLM router
│   │   └── simulator_engine.py          # 36-month SaaS sensitivity simulator
│   ├── main.py              # Application entrypoint
│   └── requirements.txt     # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # Dashboard, Partner Cockpit, Heatmaps, Charts
│   │   ├── hooks/           # useCountUp, useSimulator, useAuth
│   │   └── lib/api.js       # Client API connector
│   ├── package.json
│   └── vite.config.js
└── exports/                 # Generated deliverables (.docx, .pptx, .pdf, .xlsx)
```

---

## 🔒 Environment & Configuration (`.env`)

The backend automatically runs fully locally with **Ollama** out of the box with zero external API keys needed. If you wish to enable optional cloud providers for fallback, configure `backend/.env`:

```ini
# Local Ollama (Default)
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LOCAL_MODEL=gemma4:12b

# Optional Cloud Providers (Leave blank for 100% local/offline execution)
GROQ_API_KEY=
GEMINI_API_KEY=
NVIDIA_API_KEY=
```

---

## 📄 License
MIT License. Built for venture builders, investors, incubators, and startup founders.
