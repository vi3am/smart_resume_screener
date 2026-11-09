from app.services.scan_check import is_scanned


def test_image_only_pdf_is_scanned():
    assert is_scanned(["", ""]) is True


def test_no_pages_is_scanned():
    assert is_scanned([]) is True


def test_almost_empty_text_is_scanned():
    assert is_scanned(["page 1", "page 2"]) is True


def test_normal_cv_is_not_scanned():
    assert is_scanned(["Jane Doe\nExperience\n" + "Worked on projects. " * 20]) is False


def test_mixed_document_with_real_text_is_accepted():
    # known limitation: one real page is enough to pass
    assert is_scanned(["x" * 400, ""]) is False