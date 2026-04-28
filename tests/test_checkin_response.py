from checkin_response import is_successful_checkin_response


def test_successful_200_response_is_success() -> None:
    assert is_successful_checkin_response(200, '{"success": true}')


def test_already_checked_in_message_is_treated_as_success() -> None:
    response_text = '{"success": false, "message": "今天已完成签到，请勿重复操作"}'

    assert is_successful_checkin_response(500, response_text)


def test_unrelated_failure_message_is_not_success() -> None:
    response_text = '{"success": false, "message": "USER NOT FOUND"}'

    assert not is_successful_checkin_response(500, response_text)


def test_200_response_with_explicit_false_success_is_failure() -> None:
    response_text = '{"success": false, "message": "USER NOT FOUND"}'

    assert not is_successful_checkin_response(200, response_text)
