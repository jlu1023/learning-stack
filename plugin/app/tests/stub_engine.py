"""An engine that knows only `where` and `graph`, to check the dashboard still
draws when `unit`, `due` and `stats` are missing (an older or cut-down engine)."""
import json
import os
import sys

args = sys.argv[1:]
if args[:1] == ["where"]:
    print(json.dumps({"root": os.getcwd(), "frontend": "plain", "library": None, "courses": ["ZZ303"]}))
elif args[:1] == ["graph"]:
    print(json.dumps({"course": args[1], "nodes": [
        {"name": "One", "type": "definition", "unit": 1, "state": {"mastery": "secure"}},
        {"name": "Two", "type": "theorem", "unit": 1, "state": {"mastery": "unseen"}},
        {"name": "Proof - Two", "type": "proof", "unit": 1, "state": {"mastery": "unseen"}},
    ]}))
else:
    sys.stderr.write(f"usage: engine: invalid choice: '{args[0] if args else ''}'\n")
    sys.exit(2)
