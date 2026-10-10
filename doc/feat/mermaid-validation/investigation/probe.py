"""Record timeout-bounded SVG observations for disposable Mermaid fixtures."""

import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

root = Path(__file__).parent
inputs = json.loads((root / "inputs.json").read_text())
for name in ("sequence-original", "sequence-corrected"):
    inputs[name] = (root / (name + ".mmd")).read_text()
child = """import mermaidx,sys,json,hashlib
try:
 s=mermaidx.render(sys.stdin.read(),backend='quickjs').svg()
 print(json.dumps({'outcome':'svg','bytes':len(s.encode()),'sha256':hashlib.sha256(s.encode()).hexdigest()}))
except Exception as e:
 print(json.dumps({'outcome':'error','exception':type(e).__name__,'diagnostic':str(e)}))
 sys.exit(1)
"""
results = []
for name, source in inputs.items():
    blocks = [(1, source)]
    if name.endswith(".md"):
        # Extract these exact fixtures; this is not production Markdown support.
        blocks = []
        lines = source.splitlines(keepends=True)
        starts = [i for i, line in enumerate(lines) if line.strip() == "```mermaid"]
        for start in starts:
            end = next(
                i for i in range(start + 1, len(lines)) if lines[i].strip() == "```"
            )
            blocks.append((start + 2, "".join(lines[start + 1 : end])))
    record = {"case": name, "source": source, "fences": []}
    for line, diagram in blocks:
        try:
            proc = subprocess.run(
                [sys.executable, "-c", child],
                input=diagram,
                text=True,
                capture_output=True,
                timeout=30,
            )
            observation = {
                "markdown_content_line": line,
                "exit": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        except subprocess.TimeoutExpired as e:
            observation = {
                "markdown_content_line": line,
                "timeout_seconds": 30,
                "stdout": str(e.stdout),
                "stderr": str(e.stderr),
            }
        record["fences"].append(observation)
    record["harness_success"] = all(f.get("exit") == 0 for f in record["fences"])
    results.append(record)
    sys.stdout.write(f"{name} {record['harness_success']}\n")
    sys.stdout.flush()
output = {
    "python": sys.version,
    "platform": platform.platform(),
    "machine": platform.machine(),
    "versions": {
        p: importlib.metadata.version(p)
        for p in ("mermaidx", "quickjs-ng", "resvg-py", "termaid")
    },
    "results": results,
}
(Path(sys.argv[1]) / "results.json").write_text(json.dumps(output, indent=2) + "\n")
