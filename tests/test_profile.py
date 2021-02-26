import pytest

import time


@pytest.mark.filterwarnings('ignore:pytest.PytestUnraisableExceptionWarning')
def test_xray_tracing(caplog):
    from moto import mock_xray_client, XRaySegment
    # use another closure so mock_xray_client isn't in global scope

    @mock_xray_client
    def run_test():
        from terracotta import update_settings
        import terracotta.profile

        update_settings(XRAY_PROFILE=True)

        @terracotta.profile.trace('dummy')
        def func_to_trace():
            time.sleep(0.1)

        with XRaySegment():
            func_to_trace()

        with XRaySegment():
            with terracotta.profile.trace('dummy2'):
                time.sleep(0.1)

        for record in caplog.records:
            assert record.levelname != 'ERROR'

        # sanity check, recording without starting a segment should fail
        func_to_trace()
        assert any('cannot find the current segment' in rec.message for rec in caplog.records)

    run_test()


@pytest.mark.filterwarnings('ignore:pytest.PytestUnraisableExceptionWarning')
def test_xray_exception(caplog):
    from moto import mock_xray_client, XRaySegment
    # use another closure so mock_xray_client isn't in global scope

    @mock_xray_client
    def run_test():
        from terracotta import update_settings
        import terracotta.profile

        update_settings(XRAY_PROFILE=True)

        with XRaySegment():
            with pytest.raises(NotImplementedError):
                with terracotta.profile.trace('dummy') as subsegment:
                    raise NotImplementedError('foo')

        assert len(subsegment.cause['exceptions']) == 1
        assert subsegment.cause['exceptions'][0].message == 'foo'

    run_test()
