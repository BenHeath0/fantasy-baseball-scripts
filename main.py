#!/usr/bin/env python3
"""
Main entry point for fantasy baseball scripts.

Usage:
    python main.py <script_name> [script_args...]

Available scripts:
    calc-auction-draft-money  - Calculate auction draft money
    josebutto                  - Analyze Jose Butto data
    fantasy-football-draft     - Fantasy football draft tool
    player-evaluation          - Fantasy baseball player evaluation
    prospects                  - Prospect rankings analysis
    fantrax-scraper            - Scrape Fantrax data
"""

import argparse
import subprocess
import sys
from pathlib import Path


# Map script names to their paths
SCRIPT_MAP = {
    "calc-auction-draft-money": {
        "path": "calc-auction-draft-money/main.py",
        "description": "Calculate auction draft money",
    },
    "josebutto": {
        "path": "experiments/josebutto/main.py",
        "description": "Analyze Jose Butto data",
    },
    "fantasy-football-draft": {
        "path": "fantasy-football-draft/main.py",
        "description": "Fantasy football draft tool",
    },
    "player-evaluation": {
        "path": "player-evaluation/main.py",
        "description": "Fantasy baseball player evaluation",
    },
    "prospects": {
        "path": "prospects/main.py",
        "description": "Prospect rankings analysis",
    },
    "fantrax-scraper": {
        "path": "fantrax-scraper.py",
        "description": "Scrape Fantrax data",
    },
}


def list_scripts():
    """List all available scripts"""
    print("Available scripts:")
    print("-" * 60)
    for name, info in sorted(SCRIPT_MAP.items()):
        print(f"  {name:30} - {info['description']}")
    print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run fantasy baseball scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "script",
        nargs="?",
        help="Name of the script to run",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available scripts",
    )

    # Parse only known args to allow passing through to scripts
    args, remaining = parser.parse_known_args()

    # If --list flag is used, show scripts and exit
    if args.list:
        list_scripts()
        return

    # If no script name provided, show usage
    if not args.script:
        parser.print_help()
        sys.exit(1)

    # Check if script exists
    if args.script not in SCRIPT_MAP:
        print(f"Error: Unknown script '{args.script}'")
        print()
        list_scripts()
        sys.exit(1)

    # Get script path
    script_info = SCRIPT_MAP[args.script]
    script_path = Path(__file__).parent / script_info["path"]

    # Check if script file exists
    if not script_path.exists():
        print(f"Error: Script file not found: {script_path}")
        sys.exit(1)

    # Determine the working directory (parent of script file)
    script_dir = script_path.parent

    # Build command to run
    cmd = [sys.executable, str(script_path)] + remaining

    # Run the script in its directory
    try:
        result = subprocess.run(cmd, cwd=script_dir)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running script: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
