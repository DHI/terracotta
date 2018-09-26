def check_integrity(settings):
    db_provider = settings.get('environment_variables', {}).get('TC_DB_PROVIDER')

    if db_provider and db_provider != 'sqlite-remote':
        raise ValueError('Provider must be "sqlite-remote"')
