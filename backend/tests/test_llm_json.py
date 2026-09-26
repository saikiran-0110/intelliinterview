from app.services.llm_json import as_dict_list, as_str_list, as_text


def test_as_str_list_bare_string_becomes_one_item():
    assert as_str_list("Docker", ["fallback"]) == ["Docker"]


def test_as_str_list_never_character_splits():
    result = as_str_list("go", ["fallback"])
    assert result == ["go"]
    assert result != list("go")


def test_as_str_list_none_returns_fallback():
    assert as_str_list(None, ["fallback"]) == ["fallback"]


def test_as_str_list_passthrough_drops_empty_entries():
    assert as_str_list(["a", "", "  ", "b"], ["fallback"]) == ["a", "b"]


def test_as_str_list_empty_list_returns_fallback():
    assert as_str_list([], ["fallback"]) == ["fallback"]


def test_as_str_list_non_list_non_string_returns_fallback():
    assert as_str_list({"a": 1}, ["fallback"]) == ["fallback"]
    assert as_str_list(42, ["fallback"]) == ["fallback"]


def test_as_dict_list_passthrough_drops_non_dict_entries():
    items = [{"name": "python"}, "not-a-dict", {"name": "java"}]
    assert as_dict_list(items, []) == [{"name": "python"}, {"name": "java"}]


def test_as_dict_list_non_list_returns_fallback():
    fallback = [{"name": "fallback"}]
    assert as_dict_list("not a list", fallback) == fallback
    assert as_dict_list(None, fallback) == fallback


def test_as_dict_list_empty_returns_fallback():
    fallback = [{"name": "fallback"}]
    assert as_dict_list([], fallback) == fallback
    assert as_dict_list(["only-strings"], fallback) == fallback


def test_as_text_valid_string_passthrough():
    assert as_text("hello", "fallback") == "hello"


def test_as_text_blank_and_none_return_fallback():
    assert as_text(None, "fallback") == "fallback"
    assert as_text("   ", "fallback") == "fallback"


def test_as_text_wrong_type_returns_fallback():
    assert as_text(["a", "list"], "fallback") == "fallback"
    assert as_text({"not": "text"}, "fallback") == "fallback"
    assert as_text(42, "fallback") == "fallback"
