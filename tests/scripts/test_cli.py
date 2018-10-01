import pytest
from click.testing import CliRunner


@pytest.mark.parametrize('level', ['debug', 'info'])
def test_logging_visible(level):
    from terracotta.scripts.cli import cli

    @cli.command('dummy')
    def dummy():
        import logging
        logger = logging.getLogger('terracotta')
        logger.info('test')

    runner = CliRunner()
    result = runner.invoke(
        cli, ['--loglevel', level, 'dummy']
    )
    assert result.exit_code == 0
    assert '[+]\x1b[0m test\x1b[0m' in result.output


@pytest.mark.parametrize('level', ['warning', 'error', 'critical'])
def test_logging_invisible(level):
    from terracotta.scripts.cli import cli

    @cli.command('dummy')
    def dummy():
        import logging
        logger = logging.getLogger('terracotta')
        logger.info('test')

    runner = CliRunner()
    result = runner.invoke(
        cli, ['--loglevel', level, 'dummy']
    )
    assert result.exit_code == 0
    assert not result.output
