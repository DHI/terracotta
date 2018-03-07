import os
import configparser
from configparser import NoSectionError


DEFAULT_OPTIONS = {
   'max_cache_size': 256000000,  # 256MB
   'timestepped': False
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

    cfg = configparser.ConfigParser(defaults=DEFAULT_OPTIONS)
    cfg.read(cfg_path)

    # Validate options
    options = {}
    options['max_cache_size'] = cfg.getint('options', 'max_cache_size')

    # Validate datasets
    datasets = {}
    try:
        datasets = cfg['datasets']
        no_datasets = False
    except NoSectionError:
        no_datasets = True
    if no_datasets or not datasets.sections():
        raise ValueError('No datasets specified in config file')

    for ds_name in datasets.sections():
        ds = {}
        ds['name'] = ds_name
        ds['timestepped'] = datasets.getboolean(ds_name, timestepped)
        try:
            path = datasets.get(ds_name, 'path')
            if not os.path.isdir(path) and os.access(path, os.R_OK):
                raise ValueError('path {} in {} is not a readable directory'.format(path, ds_name))

