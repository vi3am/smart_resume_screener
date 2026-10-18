from eval.pii import find_pii, redact


def test_redacts_email_phone_url_and_handle():
    text = "Mail a.b@gmail.com, call +855 979 333 482, github.com/someone, @someone"
    out = redact(text)
    assert "gmail" not in out and "979" not in out and "someone" not in out
    assert find_pii(out) == []


def test_year_ranges_are_not_phone_numbers():
    text = "Designer 2022-2035 and 2020 - 2021"
    assert redact(text) == text
    assert find_pii(text) == []


def test_name_redaction_keeps_ordinary_words():
    out = redact("SINA BUT worked here, but left", names=["Sina But"])
    assert "SINA" not in out
    assert "but left" in out
