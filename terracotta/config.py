import os
import re
import configparser


DEFAULT_CACHE_SIZE = 256000000
DEFAULT_TIMESTEPPED = False


def default_cfg():
    return {
        'max_cache_size': DEFAULT_CACHE_SIZE,
        'timestepped': DEFAULT_TIMESTEPPED
    }


def parse_cfg(cfg_path='./config.cfg'):
    """Parse and validate config file.

    Parameters
    ----------
    cfg_path: str
        Path to config file.

    Returns
    -------
    out: (options, datasets) tuple"""

    cfg = configparser.ConfigParser()
    cfg.read(cfg_path)

    # Get options
    options = {}
    try:
        cfg_options = cfg['options']
    except KeyError:
        # Dummy section
        cfg.add_section('options')
        cfg_options = cfg['options']
    options['max_cache_size'] = cfg_options.getint('max_cache_size', fallback=DEFAULT_CACHE_SIZE)

    # Assume remaining sections are datasets
    cfg.remove_section('options')
    if not cfg.sections():
        raise ValueError('no datasets in config file')

    datasets = {}
    for ds_name in cfg.sections():
        cfg_ds = cfg[ds_name]
        ds = {}
        # Options that we have defaults for or that we know exist
        ds['name'] = ds_name
        ds['timestepped'] = cfg_ds.getboolean('timestepped', fallback=DEFAULT_TIMESTEPPED)
        # Options that must exist but don't have defaults
        try:
            path = cfg_ds['path']
            reg_str = cfg_ds['regex']
        except KeyError as e:
            raise ValueError('Missing option {} in dataset {}'.format(e.args[0], ds_name))
        # Validate option values
        if not os.path.isdir(path) and os.access(path, os.R_OK):
            raise ValueError('path {} in {} is not a readable directory'.format(path, ds_name))
        reg = re.compile(reg_str)
        if ds['timestepped'] and 'timestamp' not in reg.groupindex.keys():
            raise ValueError('missing timestamp group in regex for timestepped dataset {}'
                             .format(ds_name))
        ds['regex'] = reg
        ds['path'] = path
        datasets[ds_name] = ds

    return (options, datasets)
