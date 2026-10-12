from creator_resume_service import CreatorResumeRequest, subscriber_update


def test_new_profile_triggers_subscriber_update():
    request = CreatorResumeRequest(pdf_path=None, subscriber_id="sub-42", last_update_epoch=0)
    result = subscriber_update({"text_per_page": ["Mina - video creator"]}, request, now=86_401)
    assert result.should_send is True
    assert result.reason == "new creator profile parsed"


def test_empty_parse_does_not_trigger_update():
    request = CreatorResumeRequest(pdf_path=None, subscriber_id="sub-42", last_update_epoch=0)
    result = subscriber_update({"text_per_page": ["  "]}, request, now=86_401)
    assert result.should_send is False


def test_profile_keys_alone_do_not_count_as_parsed_page_text():
    request = CreatorResumeRequest(pdf_path=None, subscriber_id="sub-42", last_update_epoch=0)
    result = subscriber_update({"name": "Mina", "skills": ["video"]}, request, now=86_401)
    assert result.should_send is False
