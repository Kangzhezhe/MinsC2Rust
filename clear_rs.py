from pathlib import Path

ROOT = Path("/home/mins/MinsC2Rust/output")

for path in ROOT.rglob("*.rs"):
    if path.name != "lib.rs" and path.is_file():
        path.write_text("", encoding="utf-8")