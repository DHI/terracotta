from click.testing import CliRunner


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
