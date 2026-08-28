"""
AHFMES-ARE — 1-Click Secure AI Tunnel & Token Auth Launcher (ACC-721, ACC-722)

Launches the AHFMES-ARE Control Center with a cryptographically secure token,
and automatically shares the dashboard via Cloudflare Tunnel if available.
Zero external dependencies (Python Standard Library only).
"""

import os
import re
import secrets
import shutil
import subprocess
import sys
import time


def generate_token() -> str:
    token_env = os.environ.get("ARE_AUTH_TOKEN")
    if token_env and token_env.strip():
        return token_env.strip()
    return f"hermes_{secrets.token_hex(6)}"


def check_cloudflared() -> str | None:
    return shutil.which("cloudflared")


def main():
    port = int(os.environ.get("ARE_PORT", "8080"))
    token = generate_token()
    db_path = os.environ.get("ARE_DB", "are_interactive.db")

    print("\n" + "═" * 65)
    print("  🚀 AHFMES-ARE SECURE GATEWAY & AI TUNNEL LAUNCHER")
    print("═" * 65)
    print(f" • Database Path : {db_path}")
    print(f" • Port          : {port}")
    print(f" • Access Token  : {token}")
    print("─" * 65)

    # 1. Start ARE Web UI Server in background
    cmd_server = [
        sys.executable,
        "-m",
        "are.web_ui",
        "--db",
        db_path,
        "--port",
        str(port),
        "--auth-token",
        token,
    ]
    server_proc = subprocess.Popen(
        cmd_server,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    time.sleep(1.0)
    if server_proc.poll() is not None:
        out, _ = server_proc.communicate()
        print(f"❌ Failed to start ARE Web UI Server:\n{out}")
        return 1

    local_url = f"http://127.0.0.1:{port}?auth={token}"
    print(f"\n [1] LOCAL SECURE DASHBOARD:")
    print(f"     👉 {local_url}")

    # 2. Check for Cloudflare Tunnel
    cf_bin = check_cloudflared()
    cf_proc = None
    public_url = None

    if cf_bin:
        print(f"\n [2] STARTING CLOUDFLARE SECURE TUNNEL...")
        cf_cmd = [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{port}"]
        cf_proc = subprocess.Popen(
            cf_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Poll tunnel output for trycloudflare.com URL
        start_t = time.time()
        while time.time() - start_t < 15:
            if cf_proc.poll() is not None:
                break
            line = cf_proc.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue
            m = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", line)
            if m:
                public_url = f"{m.group(0)}?auth={token}"
                break

        if public_url:
            print(f"\n" + "═" * 65)
            print("  🌐 LINK PUBLIK AMAN UNTUK AI & REMOTE ACCESS:")
            print(f"  👉 {public_url}")
            print("═" * 65)
        else:
            print(" ⚠️  Tunnel aktif tetapi URL belum terdeteksi. Silakan periksa log Cloudflared.")
    else:
        print(f"\n [2] CLOUDFLARE TUNNEL (Opsional untuk Akses Publik AI):")
        print("     • cloudflared belum terinstal di PATH.")
        print("     • Untuk mengaktifkan tunnel publik 1-klik, jalankan di terminal:")
        print("       winget install --id Cloudflare.cloudflared")
        print(f"\n" + "═" * 65)
        print("  🔑 LINK LOKAL DENGAN TOKEN:")
        print(f"  👉 {local_url}")
        print("═" * 65)

    print("\n[INFO] Server berjalan. Tekan Ctrl+C untuk menghentikan server dan tunnel.\n")

    try:
        while True:
            time.sleep(1)
            if server_proc.poll() is not None:
                print("Server exited.")
                break
    except KeyboardInterrupt:
        print("\n[INFO] Menutup server dan tunnel...")
    finally:
        if server_proc.poll() is None:
            server_proc.terminate()
        if cf_proc and cf_proc.poll() is None:
            cf_proc.terminate()

    return 0


if __name__ == "__main__":
    sys.exit(main())
