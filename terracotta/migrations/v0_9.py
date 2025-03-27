up_version = (0, 9)
down_version = (0, 8)

upgrade_sql = [
    "ALTER TABLE metadata ALTER COLUMN bounds_north FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN bounds_east FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN bounds_south FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN bounds_west FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN valid_percentage FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN min FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN max FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN mean FLOAT(53)",
    "ALTER TABLE metadata ALTER COLUMN stdev FLOAT(53)",
    "UPDATE terracotta SET version='0.9.0'",
]
