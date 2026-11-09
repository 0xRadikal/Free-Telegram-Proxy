"""Execute the workflow's Bash, so heredoc binding bugs cannot hide in YAML."""
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("available", [True, False])
def test_e2e_summary_renders_results_or_missing_output_message(tmp_path, available):
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    script = next(s["run"] for s in workflow["jobs"]["e2e"]["steps"]
                  if s.get("name") == "Summary")
    out = tmp_path / "out"
    out.mkdir()
    if available:
        (out / "index.json").write_text(json.dumps({"runner": {"country": "US"},
                                                  "funnel": {"verified_links": 42}}))
        (out / "health.json").write_text(json.dumps({"sources": []}))
    summary = tmp_path / "summary.md"
    result = subprocess.run(["bash", "-e", "-o", "pipefail", "-c",
                             script.replace("/tmp/out", str(out))],
                            env=dict(os.environ, GITHUB_STEP_SUMMARY=str(summary)),
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    content = summary.read_text()
    assert "import json" not in content
    if available:
        assert "**verified_links**: 42" in content
    else:
        assert "unavailable" in content.lower()
