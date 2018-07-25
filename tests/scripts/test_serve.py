import pytest

from click.testing import CliRunner


@pytest.fixture(scope='session')
def toml_file(tmpdir_factory):
    content = """
    TILE_SIZE = [64, 64]
    """
    outfile = tmpdir_factory.mktemp('config').join('tc-config.toml')
    with open(outfile, 'w') as f:
        f.write(content)

    return outfile


def test_serve_from_pattern(raster_file):
    from terracotta.scripts import cli

    input_pattern = str(raster_file.dirpath('{name}.tif'))

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['serve', '-r', input_pattern, '--no-browser'])
    assert result.exit_code == 0


def test_serve_from_database(read_only_database):
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['serve', '-d', str(read_only_database), '--no-browser'])
    assert result.exit_code == 0


def test_serve_with_config(read_only_database, toml_file):
    from terracotta.scripts import cli

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['serve', '-d', str(read_only_database), '--no-browser',
                                     '--config', str(toml_file)])
    assert result.exit_code == 0
