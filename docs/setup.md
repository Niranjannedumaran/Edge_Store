# ⚡ Quick Setup Guide

Run EdgeStore in **3 easy steps** — just copy and paste into your terminal:

---

## 🚀 Step 1: Start EdgeStore

Open your terminal in the `EdgeStore` folder and run:

```bash
docker compose up -d --build
```

> 💡 **Windows users:** You can simply double-click [`start.bat`](file:///c:/Users/hp/Desktop/EdgeStore/start.bat) instead of using the terminal!

---

## 🌐 Step 2: Open in Your Browser

Click or visit:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🔑 Step 3: Log In

| Field | Value |
|---|---|
| **Username** | `admin` |
| **Password** | `AdminEdgeStore2026!` |

---

## 🛑 How to Stop

When you're finished, paste this command in your terminal:

```bash
docker compose down
```

> 💡 **Windows users:** You can simply double-click [`stop.bat`](file:///c:/Users/hp/Desktop/EdgeStore/stop.bat) to stop everything.

---

## 📋 Useful Commands (Cheat Sheet)

| Action | Terminal Command |
|---|---|
| **Start / Build** | `docker compose up -d --build` |
| **Stop** | `docker compose down` |
| **Check Status** | `docker compose ps` |
| **View Live Logs** | `docker compose logs -f` |
| **Restart** | `docker compose restart` |

---

## 🔐 Custom Password / Port (Optional)

If you want your own custom login password, custom port, and generated 256-bit secret key, run:

```powershell
.\deploy-own.ps1
```
*(Or double-click [`deploy-own.bat`](file:///c:/Users/hp/Desktop/EdgeStore/deploy-own.bat))*

