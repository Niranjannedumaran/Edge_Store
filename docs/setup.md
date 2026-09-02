# EdgeStore Setup Guide

This guide details setting up EdgeStore in both **Laptop Simulation Mode** (for development, testing, and evaluation) and **Raspberry Pi 4 Hardware Mode**.

---

## 1. Prerequisites

### For Laptop Simulation Development:
- Python 3.10+ (Tested up to Python 3.14)
- Node.js 18+ and npm 9+
- Git

### For Raspberry Pi 4 Physical Deployment:
- Raspberry Pi 4 Model B (4GB or 8GB recommended)
- Raspberry Pi OS (64-bit Lite, Debian Bookworm based)
- MicroSD Card (OS, minimum 16GB)
- MicroSD Card or USB Flash Drive for **Key-SD**
- 2x USB 3.0 External Hard Drives (Drive A Primary & Drive B Replica)
- USB Power Supply (5V / 3A USB-C) or UPS Battery Hat

---

## 2. Laptop Simulation Quickstart

### Step 1: Clone Repository & Create Environment
```bash
git clone <repository_url> edgestore
cd edgestore
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### Step 2: Install Python Backend Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 3: Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure `ENVIRONMENT_MODE=simulation` is set.

### Step 4: Initialize Database
```bash
python -m backend.app.db.init_db
```
Default accounts initialized:
- Administrator: `admin` / `AdminEdgeStore2026!`
- Standard Operator: `operator` / `OperatorEdgeStore2026!`

### Step 5: Install Frontend Dependencies & Start Dev Servers
In a terminal:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
In another terminal:
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://127.0.0.1:5173/` in your browser.
