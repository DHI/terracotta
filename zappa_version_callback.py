"""zappa_version_callback.py

Callback to inject correct version into deployment package
"""


def inject_version(args):
    import zipfile
    import versioneer

    with zipfile.ZipFile(args.zip_path, mode='a') as zf:
        zi = zipfile.ZipInfo('terracotta/VERSION')
        zi.external_attr = 0o755 << 16  # fix permissions
        zf.writestr(zi, versioneer.get_version())
