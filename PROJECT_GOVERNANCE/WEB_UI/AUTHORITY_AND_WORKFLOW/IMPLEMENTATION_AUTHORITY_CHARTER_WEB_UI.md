# IMPLEMENTATION AUTHORITY CHARTER — WEB_UI

Status: **RATIFIED T4 — IMPLEMENTATION AUTHORIZED**  
Fase: **WEB_UI (Localhost Control Center & Conversational Chat Copilot)**  
Aturan: `GOVERNANCE_FOLDER_STRUCTURE_RULES.md` & `ENGINEERING/RULES.md`  
Baseline: `@8323bbb`

---

## 1. Deklarasi Mandat WEB_UI

Dengan ini disahkan bahwa modul **WEB_UI** (**Localhost Control Center & Conversational Chat Copilot**) resmi berstatus **AUTHORIZED** untuk diimplementasikan.

## 2. Batasan Otoritas & Firewall

1. **Zero External Backend Dependencies:** Server web dan API backend WAJIB murni menggunakan pustaka bawaan Python Standard Library (`http.server`, `json`, `sqlite3`, `threading`, `urllib`, `dataclasses`, dll.) tanpa dependensi tambahan seperti Flask, FastAPI, atau Django.
2. **Security & Gated Execution:** Seluruh aksi eksekusi dari tombol UI atau chat copilot (seperti order, perubahan risiko, atau siklus riset) tetap WAJIB melalui tata kelola dan filter `CapitalSafetyKernel`.
3. **Responsive Glassmorphism Single Page Application:** Frontend UI dirancang modern, responsif, dan menyatu dalam format SPA yang melayani dashboard visual, grafik interaktif, dan panel obrolan AI Copilot.
4. **1-Click Windows Launcher:** Menyediakan script peluncur `.bat` yang menyederhanakan peluncuran aplikasi langsung ke browser `http://localhost:8080`.

---

```text
RATIFIED BY: Lead Architect & Auditor
DATE       : 2026-08-28
DISPOSITION: WEB_UI IMPLEMENTATION AUTHORIZED
```
