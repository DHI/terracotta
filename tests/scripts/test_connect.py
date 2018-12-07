from click.testing import CliRunner


def test_connect(test_server):
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['connect', test_server, '--no-browser'])
    assert result.exit_code == 0


def test_connect_find_socket(test_server):
    import socket
    from contextlib import closing

    from terracotta.scripts import cli

    host = '127.0.0.1'
    port = 5556

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((host, port))

        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ['connect', test_server, '--port', port, '--no-browser']
        )
        assert result.exit_code != 0
        assert 'Could not find open port to bind to' in result.output


def test_connect_invalid_port():
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['connect', 'localhost:5556', '--no-browser'])
    assert result.exit_code != 0
    assert 'Could not connect' in result.output


def test_connect_invalid_path(test_server):
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['connect', f'{test_server}/foo', '--no-browser'])
    assert result.exit_code != 0
    assert 'Could not connect' in result.output


def test_connect_version_mismatch(test_server, monkeypatch):
    from terracotta.scripts import cli
    fake_version = '0.0.0'

    with monkeypatch.context() as m:
        m.setattr('terracotta.scripts.connect.__version__', fake_version)

        runner = CliRunner()
        result = runner.invoke(cli.cli, ['connect', test_server, '--no-browser'])
        assert result.exit_code != 0
        assert fake_version in result.output
