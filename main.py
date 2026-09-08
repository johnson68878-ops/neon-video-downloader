"""程式入口；VS Code 按 F5 或 python main.py 啟動。"""
import json
import sys
from pathlib import Path

def main():
    if '--worker' in sys.argv:
        from neon.worker import worker
        with open(sys.argv[3], 'w', encoding='utf-8', buffering=1) as output:
            sys.stdout = output
            sys.stderr = output
            worker(json.loads(Path(sys.argv[2]).read_text(encoding='utf-8')))
    else:
        from neon.ui import gui
        gui()

if __name__ == '__main__':
    main()
