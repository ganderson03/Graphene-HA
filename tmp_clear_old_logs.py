from pathlib import Path
import shutil

root = Path.cwd()
removed = []

# Remove root-level legacy log dirs like logs_* and the structured logs folder.
for p in root.iterdir():
    if p.is_dir() and (p.name == "logs" or p.name.startswith("logs_")):
        shutil.rmtree(p, ignore_errors=True)
        removed.append(str(p.relative_to(root)))

# Remove previous dashboard output for a clean full-data regeneration.
out = root / "comparison_dashboard"
if out.exists() and out.is_dir():
    shutil.rmtree(out, ignore_errors=True)
    removed.append(str(out.relative_to(root)))

print("Removed:")
for r in sorted(removed):
    print(f" - {r}")
