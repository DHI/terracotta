

up_version = (0, 8)
down_version = (0, 7)

upgrade_sql = [
    # "CREATE TABLE",
    # "ALTER TABLE keys ADD COLUMN index INTEGER UNIQUE",
    # "ALTER TABLE keys RENAME TO key_names",
    "UPDATE terracotta SET version='v0.8.0'",
]

downgrade_sql = []