import sys

import pytest
from packaging.requirements import Requirement

import backend.ratio_lab as matching
from scripts import preflight


@pytest.mark.parametrize("configured", [True, False])
def test_preflight_checks_the_required_visitor_matching_environment(monkeypatch, capsys, configured):
    monkeypatch.setattr(sys, "argv", ["preflight.py"])
    monkeypatch.setattr(matching, "status", lambda: {"configured": configured})
    result = preflight.main()
    output = capsys.readouterr().out
    assert f"{'PASS' if configured else 'FAIL'} MediaPipe 추천 환경·모델·비교 기준" in output
    if not configured:
        assert result == 1


@pytest.mark.parametrize("system,machine,expected", [
    ("linux", "aarch64", "==0.10.18"),
    ("linux", "x86_64", "==0.10.21"),
    ("darwin", "x86_64", "==0.10.21"),
    ("win32", "AMD64", "==0.10.21"),
])
def test_matching_requirements_select_one_supported_mediapipe_version(system, machine, expected):
    requirements = [Requirement(line) for line in (preflight.ROOT / "requirements-landmarks.txt").read_text().splitlines()
                    if line.startswith("mediapipe==")]
    selected = [str(requirement.specifier) for requirement in requirements
                if requirement.marker.evaluate({"sys_platform": system, "platform_machine": machine})]
    assert selected == [expected]
