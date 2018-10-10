import logging


def test_logstream(caplog, capsys):
    from terracotta import logs
    assert logs.use_colors

    logger = logs.set_logger('DEBUG')
    caplog.set_level('DEBUG', logger='terracotta')
    logger.warning('test')

    log_out = caplog.records
    assert len(log_out) == 1
    log_out = log_out[0]
    assert 'test' == log_out.message
    assert logs.LEVEL_PREFIX['WARNING'] == log_out.levelshortname

    captured = capsys.readouterr()
    assert '[!]' in captured.err
    assert 'test' in captured.err


def test_logstream_nocolors(monkeypatch, caplog, capsys):
    with monkeypatch.context() as m:
        from terracotta import logs
        m.setattr(logs, 'use_colors', False)

        assert not logs.use_colors

        logger = logs.set_logger('DEBUG')
        caplog.set_level('DEBUG', logger='terracotta')
        logger.warning('test')

        log_out = caplog.records
        assert len(log_out) == 1
        log_out = log_out[0]
        assert 'test' == log_out.message
        assert logs.LEVEL_PREFIX['WARNING'] == log_out.levelshortname

        captured = capsys.readouterr()
        assert ' [!] test\n' == captured.err


def test_double_init(caplog):
    from terracotta import logs

    logs.set_logger('DEBUG')
    logs.set_logger('DEBUG')

    caplog.set_level('DEBUG', logger='terracotta')
    logger = logging.getLogger('terracotta')
    logger.warning('test')

    assert len(caplog.records) == 1
