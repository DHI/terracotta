

def test_app():
    from terracotta import update_settings
    update_settings(DEBUG=True)

    from terracotta.app import app
    assert app.debug
