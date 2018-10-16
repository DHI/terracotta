#!/usr/bin/env python3

from pathlib import Path
import os

import click

BASE_DIR = Path(__file__).parent


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('zappa_args', nargs=-1, type=click.UNPROCESSED)
@click.option('-s', '--zappa-settings', type=click.Path(exists=True, dir_okay=False),
              required=False, default='zappa_settings.toml')
def deploy(zappa_args, zappa_settings):
    try:
        import docker
    except ImportError:
        click.echo(
            'Docker Python bindings need to be installed (try `pip install docker`)', err=True
        )
        raise click.Abort()

    with open(zappa_settings, 'r') as f:
        settings_content = f.read()

    client = docker.from_env()

    click.echo('(Re-)building Docker image (this might take a while)...')
    try:
        client.images.build(
            path=str(BASE_DIR), dockerfile='package/Dockerfile', rm=True, tag='tc-deploy'
        )
    except docker.errors.BuildError as exc:
        click.echo('Error while building Docker image:', err=True)
        click.echo(exc, err=True)
        click.Abort()

    click.echo('Calling Zappa...')
    click.echo('')

    container = client.containers.create(
        image='tc-deploy', command=[zappa_settings, *zappa_args],
        auto_remove=True, stdin_open=True, environment={
            'AWS_ACCESS_KEY_ID': os.environ['AWS_ACCESS_KEY_ID'],
            'AWS_SECRET_ACCESS_KEY': os.environ['AWS_SECRET_ACCESS_KEY']
        }
    )
    container.start()

    s = container.attach_socket(params={'stdin': 1, 'stream': 1})
    s.send(settings_content.encode('utf-8'))
    s.close()

    for line in container.attach(stdout=True, stderr=True, stream=True):
        click.echo(line.decode("utf-8"), nl=False)


if __name__ == '__main__':
    deploy()
