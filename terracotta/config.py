import os
import re
import configparser
from ast import literal_eval


DEFAULT_CACHE_SIZE = 256000000
DEFAULT_TIMESTEPPED = False
DEFAULT_CATEGORICAL = False


def _parse_classes(ds_name, cfg):
    cfg_ds = cfg[ds_name]

    try:
        class_names = [s.strip() for s in cfg_ds['class_names'].split(',')]
        class_vals = [s.strip() for s in cfg_ds['class_values'].split(',')]
    except KeyError as e:
        raise ValueError('Missing {} for categorical dataset {}'.format(e.args[0], ds_name))

    # Sanity check
    if not all([s.isdigit() for s in class_vals]):
        raise ValueError('Non-numeric value in class_values for dataset {}'.format(ds_name))
    if len(class_vals) != len(class_names):
        raise ValueError('Number of class_names and class_values do not match for dataset {}'
                         .format(ds_name))

    # literal_eval converts x.y to float and x to int
    class_vals = [literal_eval(x) for x in class_vals]

    return dict(zip(class_names, class_vals))


def parse_ds(ds_name, cfg):
    cfg_ds = cfg[ds_name]
    ds = {}

    # Options that we have defaults for or that we know exist
    ds['name'] = ds_name
    ds['timestepped'] = cfg_ds.getboolean('timestepped', fallback=DEFAULT_TIMESTEPPED)
    ds['categorical'] = cfg_ds.getboolean('categorical', fallback=DEFAULT_CATEGORICAL)

    # Options that must exist but don't have defaults
    try:
        path = cfg_ds['path']
        reg_str = cfg_ds['regex']
    except KeyError as e:
        raise ValueError('Missing option {} for dataset {}'.format(e.args[0], ds_name))

    # Validate option values
    if not os.path.isdir(path) and os.access(path, os.R_OK):
        raise ValueError('path {} in {} is not a readable directory'.format(path, ds_name))
    reg = re.compile(reg_str)
    if ds['timestepped'] and 'timestep' not in reg.groupindex.keys():
        raise ValueError('missing timestep group in regex for timestepped dataset {}'
                         .format(ds_name))
    if ds['categorical']:
        ds['classes'] = _parse_classes(ds_name, cfg)

    files = os.listdir(path)
    matches = map(reg.match, files)
    matches = [x for x in matches if x is not None]
    if not matches:
        raise ValueError('no files matched {} in {}'.format(reg.pattern, path))

    # Only support 1 file per timestep for now
    if not ds['timestepped']:
        assert len(matches) == 1
        ds['file'] = matches[0].group(0)
    else:
        ds['timesteps'] = {}
        for m in matches:
            timestep = m.group('timestep')
            # Only support 1 file per timestep for now
            assert timestep not in ds['timesteps']
            ds['timesteps'][timestep] = os.path.join(path, m.group(0))

    return ds


def parse_options(cfg):
    """Parse and validate options section of config file.

    Parameters
    ----------
    cfg_path: str
        Path to config file.

    Returns
    -------
    out: options dict"""

    # Get options
    options = {}
    try:
        cfg_options = cfg['options']
    except KeyError:
        # Dummy section
        cfg.add_section('options')
        cfg_options = cfg['options']
    options['tile_cache_size'] = cfg_options.getint('tile_cache_size', fallback=DEFAULT_CACHE_SIZE)

    return options
