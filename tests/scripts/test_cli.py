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


def test_entrypoint(monkeypatch, capsys):
    import sys
    from terracotta.scripts.cli import entrypoint

    with monkeypatch.context() as m:
        m.setattr(sys, 'argv', ['terracotta'])
        with pytest.raises(SystemExit) as exc:
            entrypoint()
            assert exc.code == 0

    captured = capsys.readouterr()
    assert 'Usage:' in captured.out


def test_entrypoint_exception(monkeypatch, capsys):
    import sys
    from terracotta.scripts.cli import cli, entrypoint

    dummy_error_message = 'Dummy error message'

    @cli.command('dummy')
    def dummy():
        raise RuntimeError(dummy_error_message)

    with monkeypatch.context() as m:
        m.setattr(sys, 'argv', ['terracotta', 'dummy'])
        with pytest.raises(SystemExit) as exc:
            entrypoint()
            assert exc.code == 1

    captured = capsys.readouterr()
    assert 'Uncaught exception' in captured.err
    assert dummy_error_message in captured.err
