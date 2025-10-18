from pathlib import Path

ROOT = Path(__file__).resolve().parent / "output"

if ROOT.exists():
    for path in ROOT.rglob("*.rs"):
        if not path.is_file():
            continue
        try:
            rel_path = path.relative_to(ROOT)
        except ValueError:
            rel_path = path
        if rel_path.as_posix() == "src/lib.rs":
            continue
        path.write_text("", encoding="utf-8")