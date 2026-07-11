from app.chat import generate_reply


def test_generate_reply_echoes_message():
    assert generate_reply("hello") == "hello"


def test_generate_reply_echoes_empty_string():
    assert generate_reply("") == ""
