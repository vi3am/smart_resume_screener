import spacy


def test_resume_parser_spacy_model_is_loadable():
    model = spacy.load("en_core_web_sm")

    assert model.meta["name"] == "core_web_sm"
