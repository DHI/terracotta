"""scripts/migrate.py

Migrate databases between Terracotta versions.
"""

from typing import Tuple

import click
import sqlalchemy as sqla

from terracotta import get_driver, __version__
from terracotta.migrations import MIGRATIONS


def parse_version(verstr: str) -> Tuple[int]:
    """Convert 'v<major>.<minor>.<patch>' to (major, minor, patch)"""
    components = verstr.split(".")
    components[0] = components[0].lstrip("v")
    return tuple(int(c) for c in components[:3])


def join_version(vertuple: Tuple[int]) -> str:
    return "v" + ".".join(map(str, vertuple))


@click.argument("DATABASE", required=True)
@click.option("--from", "from_version", required=False, default=None)
@click.option("--to", "to_version", required=False, default=__version__)
@click.option("-y", "--yes", "yes", is_flag=True, help="Do not ask for confirmation.")
@click.command("migrate")
def migrate(database: str, to_version: str, from_version: str, yes: bool):
    from_version, to_version, tc_version = (
        parse_version(v)[:2] if v else None
        for v in (from_version, to_version, __version__)
    )

    driver = get_driver(database)

    if to_version > tc_version:
        raise ValueError(
            f"Unknown target version {join_version(to_version)} (this is {join_version(tc_version)}). Try upgrading terracotta."
        )

    if from_version is None:
        try:
            with driver.connect(verify=False):
                from_version = parse_version(driver.db_version)[:2]
        except Exception as e:
            raise RuntimeError("Cannot determine database version.") from e

    if from_version == to_version:
        click.echo("Already at target version, nothing to do.")
        return

    migration_chain = []
    current_version = from_version

    while current_version != to_version:
        if current_version not in MIGRATIONS:
            raise RuntimeError("Unexpected error")

        migration = MIGRATIONS[current_version]
        migration_chain.append(migration)
        current_version = migration.up_version

    click.echo("Upgrade path found\n")

    for migration in migration_chain:
        click.echo(
            f"{join_version(migration.down_version)} -> {join_version(migration.up_version)}"
        )

        for cmd in migration.upgrade_sql:
            click.echo(f"    {cmd}")

        click.echo("")

    click.echo(
        f"This will upgrade the database from {join_version(from_version)} -> {join_version(to_version)} and execute the above SQL commands."
    )

    if not yes:
        click.confirm("Continue?", abort=True)

    with driver.connect(verify=False):
        for migration in migration_chain:
            for cmd in migration.upgrade_sql:
                driver.meta_store._connection.execute(sqla.text(cmd))
