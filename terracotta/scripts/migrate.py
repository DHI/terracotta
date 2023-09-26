"""scripts/migrate.py

Migrate databases between Terracotta versions.
"""

from typing import Tuple

import click
import sqlalchemy as sqla

from terracotta import get_driver, __version__
from terracotta.migrations import MIGRATIONS
from terracotta.drivers.relational_meta_store import RelationalMetaStore


def parse_version(verstr: str) -> Tuple[int, ...]:
    """Convert 'v<major>.<minor>.<patch>' to (major, minor)"""
    components = verstr.split(".")
    components[0] = components[0].lstrip("v")
    return tuple(int(c) for c in components[:2])


def join_version(vertuple: Tuple[int, ...]) -> str:
    return "v" + ".".join(map(str, vertuple))


@click.argument("DATABASE", required=True)
@click.option("--from", "from_version", required=False, default=None)
@click.option("--to", "to_version", required=False, default=__version__)
@click.option("-y", "--yes", is_flag=True, help="Do not ask for confirmation.")
@click.command("migrate")
def migrate(database: str, to_version: str, from_version: str, yes: bool) -> None:
    """Migrate databases between Terracotta versions."""
    driver = get_driver(database)
    meta_store = driver.meta_store
    assert isinstance(meta_store, RelationalMetaStore)

    to_version_tuple = parse_version(to_version)
    tc_version_tuple = parse_version(__version__)

    if to_version_tuple > tc_version_tuple:
        raise ValueError(
            f"Unknown target version {join_version(to_version_tuple)} (this is {join_version(tc_version_tuple)}). Try upgrading terracotta."
        )

    if from_version is None:
        try:  # type: ignore
            with meta_store.connect(verify=False):
                from_version_tuple = parse_version(driver.db_version)
        except Exception as e:
            raise RuntimeError("Cannot determine database version.") from e
    else:
        from_version_tuple = parse_version(from_version)

    if from_version_tuple == to_version_tuple:
        click.echo("Already at target version, nothing to do.")
        return

    migration_chain = []
    current_version = from_version_tuple

    while current_version != to_version_tuple:
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
        f"This will upgrade the database from {join_version(from_version_tuple)} -> {join_version(to_version_tuple)} and execute the above SQL commands."
    )

    if not yes:
        click.confirm("Continue?", abort=True)

    with meta_store.connect(verify=False) as conn:
        for migration in migration_chain:
            for cmd in migration.upgrade_sql:
                conn.execute(sqla.text(cmd))
