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
    port = 5000

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((host, port))

        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ['connect', test_server, '--port', '5000', '--no-browser']
        )
        assert result.exit_code != 0
        assert 'Could not find open port to bind to' in result.output
