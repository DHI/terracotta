from click.testing import CliRunner


def test_create_database(raster_file, tmpdir):
    from terracotta.scripts import cli

    outfile = tmpdir / 'out.sqlite'
    input_pattern = str(raster_file.dirpath('{name}.tif'))

    runner = CliRunner()
    result = runner.invoke(cli.cli, ['create-database', input_pattern, '-o', str(outfile)])
    assert result.exit_code == 0
    assert outfile.check()

    from terracotta import get_driver
    driver = get_driver(str(outfile), provider='sqlite')
    assert driver.key_names == ('name',)
    assert driver.get_datasets() == {('img',): str(raster_file)}


def test_create_database_rgb_key(raster_file, tmpdir):
    from terracotta.scripts import cli

    outfile = tmpdir / 'out.sqlite'
    input_pattern = str(raster_file.dirpath('{rgb}m{foo}.tif'))

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ['create-database', input_pattern, '-o', str(outfile), '--rgb-key', 'rgb']
    )
    assert result.exit_code == 0
    assert outfile.check()

    from terracotta import get_driver
    driver = get_driver(str(outfile), provider='sqlite')
    assert driver.key_names == ('foo', 'rgb')
    assert driver.get_datasets() == {('g', 'i'): str(raster_file)}


def test_create_database_invalid_rgb_key(raster_file, tmpdir):
    from terracotta.scripts import cli

    outfile = tmpdir / 'out.sqlite'
    input_pattern = str(raster_file.dirpath('{rgb}m{foo}.tif'))

    runner = CliRunner()
    result = runner.invoke(
        cli.cli, ['create-database', input_pattern, '-o', str(outfile), '--rgb-key', 'bar']
    )
    assert result.exit_code != 0
    assert not outfile.check()
