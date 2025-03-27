up_version = (0, 9)
down_version = (0, 8)

upgrade_sql = [
    "ALTER TABLE metadata ALTER COLUMN bounds_north TYPE FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN bounds_east TYPE FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN bounds_south TYPE FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN bounds_west TYPE FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN valid_percentage TYPE FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN min TYPE FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN max TYPE FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN mean TYPE FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN stdev TYPE FLOAT(53)",
    "UPDATE terracotta SET version='0.9.0'",
]
