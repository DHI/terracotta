import logging


def test_logstream(caplog):
    caplog.set_level('DEBUG', logger='terracotta')

    from terracotta import logs
    logs.set_logger('DEBUG')

    logger = logging.getLogger('terracotta')
    logger.warning('test')

    out = caplog.records
    assert len(out) == 1
    out = out[0]
    assert 'test' in out.message
    assert logs.LEVEL_PREFIX['WARNING'] == out.levelname

    logs.set_logger('WARNING')


def test_logstream_nocolors(monkeypatch, caplog):
    caplog.set_level('DEBUG', logger='terracotta')

    with monkeypatch.context() as m:
        from terracotta import logs
        m.setattr(logs, 'use_colors', False)

        logs.set_logger('DEBUG')

        logger = logging.getLogger('terracotta')
        logger.warning('test')

        out = caplog.records
        assert len(out) == 1
        out = out[0]
        assert 'test' in out.message
        assert logs.LEVEL_PREFIX['WARNING'] == out.levelname

        logs.set_logger('WARNING')


def test_logfile(tmpdir):
    from terracotta import logs
    logfile = str(tmpdir / 'tc_log.txt')
    logs.set_logger('DEBUG', logfile)

    logger = logging.getLogger('terracotta')
    logger.warning('test')

    with open(logfile) as f:
        assert '[!] test' in f.read()

    logs.set_logger('WARNING')
