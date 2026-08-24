"""Quick-launch script for the How to Fish trainer."""

import sys
from pathlib import Path

# Ensure src/ is in sys.path when executed directly from repository root
sys_src = str(Path(__file__).parent / "src")
if sys_src not in sys.path:
    sys.path.insert(0, sys_src)

from howtofish_cheat.__main__ import main

if __name__ == "__main__":
    main()
