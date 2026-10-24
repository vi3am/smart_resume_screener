from eval.check_leaks import main


def test_check_leaks_ignores_name_fragments_in_company_names(tmp_path, monkeypatch, capsys):
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("file,names\nresume.pdf,Emma Warner\n", encoding="utf-8")
    cv_dir = tmp_path / "cvs"
    cv_dir.mkdir()
    (cv_dir / "cv_01.txt").write_text(
        "Worked at Warner & Spencer.", encoding="utf-8"
    )

    monkeypatch.setattr("eval.check_leaks.MANIFEST", manifest)
    monkeypatch.setattr("eval.check_leaks.DATA_DIR", tmp_path)
    monkeypatch.setattr("eval.dataset.DATA_DIR", tmp_path)
    (tmp_path / "cvs").mkdir(exist_ok=True)

    assert main() == 0
    assert "No manifest names found" in capsys.readouterr().out


def test_check_leaks_detects_complete_name(tmp_path, monkeypatch, capsys):
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("file,names\nresume.pdf,Emma Warner\n", encoding="utf-8")
    cv_dir = tmp_path / "cvs"
    cv_dir.mkdir()
    (cv_dir / "cv_01.txt").write_text(
        "Candidate: Emma Warner", encoding="utf-8"
    )

    monkeypatch.setattr("eval.check_leaks.MANIFEST", manifest)
    monkeypatch.setattr("eval.check_leaks.DATA_DIR", tmp_path)

    assert main() == 1
    assert "1 possible leak(s)." in capsys.readouterr().out
