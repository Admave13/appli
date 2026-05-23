#!/usr/bin/env python3
"""
start.py — Arranca appli. (FastAPI + React/Vite)

    python start.py

Backend  → http://localhost:8000  (uvicorn --reload)
Frontend → http://localhost:3000  (Vite HMR)
"""

import os, sys, subprocess
from pathlib import Path

ROOT     = Path(__file__).parent
FRONTEND = ROOT / "frontend"
IS_WIN   = sys.platform == "win32"

RESET  = "\033[0m"; BOLD = "\033[1m"
GREEN  = "\033[32m"; YELLOW = "\033[33m"
CYAN   = "\033[36m"; RED    = "\033[31m"

def run(cmd, **kwargs):
    """Ejecuta un comando. En Windows usa shell=True para encontrar npm/npx."""
    return subprocess.Popen(
        cmd if not IS_WIN else " ".join(cmd),
        shell=IS_WIN,
        **kwargs,
    )

def ensure_node_modules():
    if not (FRONTEND / "node_modules").exists():
        print(f"{YELLOW}  Instalando dependencias npm (solo la primera vez)…{RESET}")
        subprocess.run(
            "npm install" if IS_WIN else ["npm", "install"],
            cwd=FRONTEND, shell=IS_WIN, check=True,
        )
        print()

def main():
    print(f"\n{BOLD}{GREEN}  appli.{RESET}  —  React + FastAPI\n")
    print(f"  {CYAN}Backend {RESET} → http://localhost:8000")
    print(f"  {CYAN}Frontend{RESET} → http://localhost:3000")
    print(f"\n  {BOLD}Ctrl+C{RESET} para parar todo.\n")

    ensure_node_modules()

    procs = []
    try:
        procs.append(run(
            [sys.executable, "-m", "uvicorn", "api:app",
             "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=ROOT,
        ))
        procs.append(run(
            ["npm", "run", "dev"],
            cwd=FRONTEND,
        ))
        procs[1].wait()

    except KeyboardInterrupt:
        print(f"\n{YELLOW}  Parando…{RESET}")
    finally:
        for p in procs:
            try:
                p.terminate(); p.wait(timeout=4)
            except Exception:
                p.kill()
        print(f"{GREEN}  ¡Hasta luego!{RESET}\n")

if __name__ == "__main__":
    main()
