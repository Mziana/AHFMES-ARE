"""
ARE Launcher -- One command to bring ARE alive.

Usage:
    python arelauncher.py              # Start live
    python arelauncher.py --dry-run    # Paper trading
    python arelauncher.py --status     # Check if running
    python arelauncher.py --dashboard  # Just show 7 TF RSI

Or after pip install -e .:
    arelauncher                        # Start live
    arelauncher --dry-run              # Paper trading
"""
import sys
import os

# Make sure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        return

    from are.trading.engine import ARELiveEngine
    engine = ARELiveEngine()

    if "--status" in args:
        pid_file = engine._pid_file
        if os.path.exists(pid_file):
            with open(pid_file) as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)
                print(f"ARE is ALIVE (PID {pid})")
            except ProcessLookupError:
                print(f"ARE is DEAD (stale PID {pid})")
        else:
            print("ARE is SLEEPING (not started)")
        return

    if "--dashboard" in args or "-d" in args:
        engine.print_dashboard()
        return

    dry_run = "--dry-run" in args

    # Override config from args
    for a in args:
        if a.startswith("--lot="):
            engine.update_config(lot=float(a.split("=")[1]))
        elif a.startswith("--tp="):
            engine.update_config(tp_points=int(a.split("=")[1]))
        elif a.startswith("--sl="):
            engine.update_config(sl_points=int(a.split("=")[1]))
        elif a.startswith("--symbol="):
            engine.update_config(symbol=a.split("=")[1])

    print("=" * 60)
    print("  ARE LAUNCHER")
    print("  Bringing the brain to life...")
    print("=" * 60)

    engine.start(dry_run=dry_run)


if __name__ == "__main__":
    main()
