from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
UI = ROOT / "ui"

def path(*parts):
    return ROOT.joinpath(*parts)
