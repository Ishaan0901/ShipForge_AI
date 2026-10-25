from app.tools.code_tools import run_code


def test_run_code_timeout(tmp_path):
    file = tmp_path / 'main.py'
    file.write_text('while True: pass')

    result = run_code(str(file))

    assert result[0] == -1
    assert 'Timeout' in result[1]