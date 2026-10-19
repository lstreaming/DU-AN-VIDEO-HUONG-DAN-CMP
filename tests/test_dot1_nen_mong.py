import sys
import pytest
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path

from src.gates.kiem_dau_phien import check_disk_thresholds, check_project_drive, check_temp_paths, run_checks, scan_project_for_secrets, scan_text_for_secrets
from src.gates.quet_vo_rong import find_empty_shells

ROOT = Path(__file__).resolve().parents[1]


def test_four_authority_anchors_and_pointer_are_present():
    ledger_path = ROOT / "du_lieu" / "SO_VIEC.md"
    requirements_path = ROOT / "du_lieu" / "YEU_CAU_C2.md"
    if not ledger_path.is_file() or not requirements_path.is_file():
        pytest.skip("private handoff records are not included in the public source mirror")
    ledger = ledger_path.read_text(encoding="utf-8").splitlines()
    requirements = requirements_path.read_text(encoding="utf-8")
    assert ledger[0] == "## 🎯 CON TRỎ"
    assert sum(line.strip().startswith("## 🎯 CON TRỎ") for line in ledger) == 1
    assert len(ledger) <= 400
    required_terms = {
        "C2-M01": ("900 giây", "15 phút"),
        "C2-M02": ("Huy Tưởng", "Xuân Công", "nguồn"),
        "C2-M03": ("c172", "C2-200", "HandRig"),
        "C2-M04": ("C2-188", "Windows", "ổ C", "du_lieu/khoa/", "du_lieu/tam_me/"),
    }
    for anchor, terms in required_terms.items():
        assert anchor in requirements
        assert all(term in requirements for term in terms)


def test_disk_thresholds_fail_closed():
    assert check_disk_thresholds(10.0, 15.0)
    assert check_disk_thresholds(9.99, 20.0)
    assert check_disk_thresholds(20.0, 14.99)
    assert check_disk_thresholds(20.0, 20.0) == []


def test_temp_paths_must_be_project_local(tmp_path):
    expected_path = tmp_path / "du_lieu" / "tam_me"
    expected_path.mkdir(parents=True)
    expected = str(expected_path)
    assert check_temp_paths(tmp_path, {"TEMP": expected, "TMP": expected}) == []
    issues = check_temp_paths(tmp_path, {"TEMP": "C:\\Temp", "TMP": expected})
    assert "TEMP_khong_o_du_lieu_tam_me" in issues


def test_temp_paths_require_existing_temp_directory(tmp_path):
    temp_dir = tmp_path / "du_lieu" / "tam_me"
    issues = check_temp_paths(tmp_path, {"TEMP": str(temp_dir), "TMP": str(temp_dir)})
    assert "thu_muc_du_lieu_tam_me_khong_ton_tai" in issues
    temp_dir.mkdir(parents=True)
    assert check_temp_paths(tmp_path, {"TEMP": str(temp_dir), "TMP": str(temp_dir)}) == []


def test_secret_patterns_detect_synthetic_credentials():
    pem_marker = "-----BEGIN " + "RSA PRIVATE KEY" + "-----"
    samples = (
        ("GitHub Token", "ghp_" + ("A" * 20)),
        ("GitHub Fine-Grained PAT", "github_pat_" + ("B" * 20)),
        ("Telegram Bot Token", "1234567890:" + ("C" * 30)),
        ("API Secret Key", "sk-" + ("D" * 20)),
        ("AWS Access Key", "AKIA" + ("E" * 16)),
        ("Cloud API Key", "AIza" + ("F" * 30)),
        ("Cloudflare API Token", "cfat_" + ("H" * 24)),
        ("Cloudflare User Token", "cfut_" + ("L" * 24)),
        ("Groq API Key", "gsk_" + ("J" * 20)),
        ("Slack Token", "xoxb-" + ("G" * 10)),
        ("PEM Private Key", pem_marker),
    )
    for label, sample in samples:
        assert label in scan_text_for_secrets(sample)
    assert scan_text_for_secrets("documentation contains no credential") == []


def test_preflight_mutation_turns_red_for_c_drive_temp():
    project_temp = str(ROOT / "du_lieu" / "tam_me")
    issues = run_checks(
        ROOT,
        environ={"TEMP": "C:\\Temp", "TMP": project_temp},
        project_free_gb=46.0,
        c_free_gb=17.0,
    )
    assert "TEMP_khong_o_du_lieu_tam_me" in issues


def test_preflight_rejects_missing_temp_and_low_disk_space():
    project_temp = str(ROOT / "du_lieu" / "tam_me")
    issues = run_checks(
        ROOT,
        environ={"TEMP": project_temp},
        project_free_gb=10.0,
        c_free_gb=15.0,
    )
    assert "TMP_chua_duoc_dat" in issues
    assert any(issue.startswith("O_du_an_duoi_10GB:") for issue in issues)
    assert any(issue.startswith("Canh_bao_o_C_duoi_15GB:") for issue in issues)


def test_empty_shell_gate_finds_stubs(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "real.py").write_text("def ready():\n    return True\n", encoding="utf-8")
    (tmp_path / "tests" / "stub.py").write_text("raise NotImplementedError\n", encoding="utf-8")
    issues = find_empty_shells(tmp_path)
    assert any("chua_cai_dat" in item for item in issues)


def test_empty_shell_gate_detects_noop_callable_beside_working_code(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    module = "def ready():\n    return True\n\ndef unfinished():\n    pass\n"
    (tmp_path / "src" / "mixed.py").write_text(module, encoding="utf-8")
    issues = find_empty_shells(tmp_path)
    assert any("vo_rong_callable:src\\mixed.py:unfinished" in item for item in issues)


def test_empty_shell_gate_reports_syntax_errors(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    issues = find_empty_shells(tmp_path)
    assert any("khong_hop_le:src\\broken.py:SyntaxError" in item for item in issues)


def test_preflight_rejects_missing_gitignore_rules(tmp_path):
    (tmp_path / "du_lieu").mkdir()
    (tmp_path / "BAT_DAU.md").write_text("guide\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("*.wav\n", encoding="utf-8")
    (tmp_path / "du_lieu" / "SO_VIEC.md").write_text("## 🎯 CON TRỎ\n", encoding="utf-8")
    (tmp_path / "du_lieu" / "YEU_CAU_C2.md").write_text(
        "C2-M01 900 giây 15 phút C2-M02 Huy Tưởng Xuân Công nguồn "
        "C2-M03 c172 C2-200 HandRig C2-M04 C2-188 Windows ổ C "
        "du_lieu/khoa/ du_lieu/tam_me/",
        encoding="utf-8",
    )
    temp_dir = str(tmp_path / "du_lieu" / "tam_me")
    issues = run_checks(
        tmp_path,
        environ={"TEMP": temp_dir, "TMP": temp_dir},
        project_free_gb=20,
        c_free_gb=20,
    )
    assert "thieu_gitignore_rule:/du_lieu/khoa/" in issues
    assert "thieu_gitignore_rule:/du_lieu/SO_VIEC.md" in issues
    assert "thieu_gitignore_rule:/du_lieu/YEU_CAU_C2.md" in issues
    assert "thieu_gitignore_rule:/du_lieu/LENH_BAN_GIAO_AI.md" in issues
    assert "thieu_gitignore_rule:/du_lieu/tam_me/" in issues
    assert "thieu_gitignore_rule:*.env" in issues


def test_preflight_rejects_project_outside_e_drive():
    assert check_project_drive("C:") == ["du_an_khong_nam_tren_o_E:C:"]
    assert check_project_drive("E:") == []


def test_preflight_checks_line_cap_and_all_four_authority_anchors(tmp_path):
    (tmp_path / "du_lieu").mkdir()
    (tmp_path / "du_lieu" / "SO_VIEC.md").write_text(
        "## 🎯 CON TRỎ\n" + "x\n" * 400,
        encoding="utf-8",
    )
    (tmp_path / "du_lieu" / "YEU_CAU_C2.md").write_text(
        "C2-M01 C2-M02 C2-M03",
        encoding="utf-8",
    )
    tmp_dir = str(tmp_path / "du_lieu" / "tam_me")
    issues = run_checks(
        tmp_path,
        environ={"TEMP": tmp_dir, "TMP": tmp_dir},
        project_free_gb=20,
        c_free_gb=20,
    )
    assert any("SO_VIEC_vuot_400_dong" in issue for issue in issues)
    assert any(issue.startswith("thieu_neo:C2-M04:") for issue in issues)


def test_start_guide_and_gitignore_match_handoff_contract():
    guide = (ROOT / "BAT_DAU.md").read_text(encoding="utf-8").splitlines()
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    rules = {line.strip() for line in ignore if line.strip() and not line.lstrip().startswith("#")}
    assert len(guide) <= 25
    assert any("du_lieu/LENH_BAN_GIAO_AI.md" in line for line in guide)
    assert any("Không xóa/di chuyển/tải dữ liệu" in line for line in guide)
    assert "$projectRoot = (Get-Location).Path" in "\n".join(guide)
    assert "$env:TEMP = Join-Path $projectRoot 'du_lieu\\tam_me'" in "\n".join(guide)
    assert "$env:TMP = $env:TEMP" in "\n".join(guide)
    assert "/du_lieu/khoa/" in rules
    assert "/du_lieu/SO_VIEC.md" in rules
    assert "/du_lieu/YEU_CAU_C2.md" in rules
    assert "/du_lieu/LENH_BAN_GIAO_AI.md" in rules
    assert "/du_lieu/tam_me/" in rules
    assert "/du_lieu/san_xuat/" in rules
    assert "*.wav" in rules
    assert "*.mp4" in rules
    assert "/khoa/" in rules
    assert ".env" in rules
    assert ".env.*" in rules
    assert "*.env" in rules
    assert "*.pem" in rules
    assert "*.key" in rules
    assert "*.p12" in rules
    assert "*.pfx" in rules
    assert "*.jks" in rules
    assert "*.keystore" in rules
    assert "*.crt" in rules
    assert "*.cer" in rules
    assert "*.token" in rules
    assert "*credentials*.json" in rules
    assert all(not ("#" in line and not line.lstrip().startswith("#")) for line in ignore)


def test_python_files_configure_utf8_at_startup():
    python_files = list((ROOT / "src").rglob("*.py")) + list((ROOT / "tests").rglob("*.py"))
    assert python_files
    for path in python_files:
        header = path.read_text(encoding="utf-8").splitlines()[:3]
        normalized = " ".join(header).replace("'", "\"")
        assert "sys.stdout.reconfigure(encoding=\"utf-8\", errors=\"replace\")" in normalized


def test_full_project_secret_scan_finds_credentials_in_env_file(tmp_path):
    project = tmp_path / "tam_me" / "copied-project"
    project.mkdir(parents=True)
    env_file = project / ".env"
    fake_token = "ghp_" + ("A" * 24)
    env_file.write_text("TOKEN=" + fake_token, encoding="utf-8")
    findings = scan_project_for_secrets(project)
    assert any("GitHub Token:.env" in item for item in findings)


def test_full_project_secret_scan_checks_named_env_files(tmp_path):
    project = tmp_path / "workspace"
    project.mkdir()
    named_env = project / "settings.env"
    named_env.write_text("TOKEN=" + "gsk_" + ("K" * 24), encoding="utf-8")
    findings = scan_project_for_secrets(project)
    assert any("Groq API Key:settings.env" in item for item in findings)


def test_full_project_secret_scan_does_not_skip_project_named_like_temp_dir(tmp_path):
    project = tmp_path / "tam_me" / "copied-project"
    project.mkdir(parents=True)
    target = project / "settings.ini"
    target.write_text("token=" + ("sk-" + ("Z" * 24)), encoding="utf-8")
    findings = scan_project_for_secrets(project)
    assert any("API Secret Key:settings.ini" in item for item in findings)


def test_full_preflight_fails_for_fake_token_in_project_copy(tmp_path):
    project = tmp_path / "copied-project"
    data = project / "du_lieu"
    data.mkdir(parents=True)
    (project / "BAT_DAU.md").write_text("guide", encoding="utf-8")
    (project / ".gitignore").write_text(
        "/du_lieu/khoa/\n/du_lieu/tam_me/\n/du_lieu/san_xuat/\n*.wav\n*.mp4\n",
        encoding="utf-8",
    )
    (data / "SO_VIEC.md").write_text("## 🎯 CON TRỎ\n", encoding="utf-8")
    (data / "YEU_CAU_C2.md").write_text(
        "C2-M01 900 giây 15 phút C2-M02 Huy Tưởng Xuân Công nguồn "
        "C2-M03 c172 C2-200 HandRig C2-M04 C2-188 Windows ổ C "
        "du_lieu/khoa/ du_lieu/tam_me/",
        encoding="utf-8",
    )
    (project / ".env").write_text("TOKEN=" + "ghp_" + ("Q" * 24), encoding="utf-8")
    temp_dir = str(data / "tam_me")
    issues = run_checks(
        project,
        environ={"TEMP": temp_dir, "TMP": temp_dir},
        project_free_gb=20,
        c_free_gb=20,
    )
    assert any(issue.startswith("GitHub Token:") for issue in issues)


def test_workspace_has_no_empty_shells():
    assert find_empty_shells(ROOT) == []
