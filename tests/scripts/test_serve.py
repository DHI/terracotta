import pytest

from click.testing import CliRunner


@pytest.fixture(scope='session')
def toml_file(tmpdir_factory):
    content = """
    DEFAULT_TILE_SIZE = [64, 64]
    """
    outfile = tmpdir_factory.mktemp('config').join('tc-config.toml')
    with open(outfile, 'w') as f:
        f.write(content)

    return outfile


def test_serve_from_pattern(raster_file):
    from terracotta.scripts import cli

    input_pattern = str(raster_file.dirpath('{name}.tif'))

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['serve', '-r', input_pattern])
    assert result.exit_code == 0


def test_serve_from_database(testdb):
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['serve', '-d', str(testdb)])
    assert result.exit_code == 0


def test_serve_no_args(testdb):
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['serve'])
    assert result.exit_code != 0


def test_serve_with_config(testdb, toml_file):
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['--config', str(toml_file), 'serve',
                                     '-d', str(testdb)])
    assert result.exit_code == 0


def test_serve_rgb_key(raster_file):
    from terracotta.scripts import cli

    input_pattern = str(raster_file.dirpath('{rgb}m{foo}.tif'))

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ['serve', '-r', input_pattern, '--rgb-key', 'rgb']
    )
    assert result.exit_code == 0


def test_serve_invalid_rgb_key(raster_file):
    from terracotta.scripts import cli

    input_pattern = str(raster_file.dirpath('{rgb}m{foo}.tif'))

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ['serve', '-r', input_pattern, '--rgb-key', 'bar']
    )
    assert result.exit_code != 0


def test_serve_find_socket(raster_file):
    import socket
    from contextlib import closing

    from terracotta.scripts import cli

    input_pattern = str(raster_file.dirpath('{name}.tif'))

    host = '127.0.0.1'
    port = 5000

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind((host, port))

        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ['serve', '-r', input_pattern, '--port', '5000']
        )
        assert result.exit_code != 0
        assert 'Could not find open port to bind to' in result.output

        runner = CliRunner()
        result = runner.invoke(cli.cli, ['serve', '-r', input_pattern])
        assert result.exit_code == 0
