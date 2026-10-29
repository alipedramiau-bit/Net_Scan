"""Remove leftover test databases from catalog + disk (one-off cleanup)."""
import sys, os, json
sys.path.insert(0, "/home/z/my-project/backend")
os.chdir("/home/z/my-project")
from pathlib import Path
import db

for name in ("test_report_fix", "__test_report_fix"):
    p = Path("databases") / f"{name}.db"
    if p.is_file():
        p.unlink()
        print("removed file:", p)
cat_path = Path("databases/catalog.json")
cat = json.loads(cat_path.read_text(encoding="utf-8"))
before = list(cat["databases"])
cat["databases"] = [x for x in cat["databases"] if x not in ("test_report_fix", "__test_report_fix")]
if cat["databases"] != before:
    cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2), encoding="utf-8")
    print("catalog updated:", cat["databases"])
print("final catalog:", db.list_databases()["databases"])
