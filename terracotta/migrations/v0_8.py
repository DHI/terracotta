up_version = (0, 8)
down_version = (0, 7)

upgrade_sql = [
    "CREATE TABLE key_names (key_name TEXT PRIMARY KEY, description TEXT, idx INTEGER UNIQUE)",
    "INSERT INTO key_names (key_name, description, idx) SELECT key, description, row_number() over (order by (select NULL)) FROM keys",
    "ALTER TABLE datasets RENAME COLUMN filepath TO path",
    "UPDATE terracotta SET version='0.8.0'",
]
