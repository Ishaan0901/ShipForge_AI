from app.tools.github_tools import scan_secrets


def test_scan_finds_fake_token(tmp_path):
    file = tmp_path / 'main.py'
    file.write_text("token = 'ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'")

    found = scan_secrets(str(tmp_path))

    assert len(found) == 1
    assert found[0]['type'] == 'GitHub token'