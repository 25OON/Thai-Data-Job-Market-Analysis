import argparse
import csv
from pathlib import Path


def sql_value(value):
    if value is None or value == "":
        return "NULL"
    escaped = value.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def main():
    parser = argparse.ArgumentParser(description="Convert CSV to a MySQL .sql script")
    parser.add_argument("csv_path")
    parser.add_argument("--table", default="raw_jobs")
    parser.add_argument("--db", default="jobthai")
    parser.add_argument("--out", help="Output .sql path (default: same name as the CSV)")
    args = parser.parse_args()

    out_path = args.out or str(Path(args.csv_path).with_suffix(".sql"))

    with open(args.csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        rows = list(reader)

    lines = [
        "SET NAMES utf8mb4;",
        f"CREATE DATABASE IF NOT EXISTS `{args.db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        f"USE `{args.db}`;",
        "",
        # Raw staging table: everything is text, cleaning happens later in SQL
        f"DROP TABLE IF EXISTS `{args.table}`;",
        f"CREATE TABLE `{args.table}` (",
        ",\n".join(f"    `{c}` TEXT" for c in columns),
        ") CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        "",
    ]

    col_list = ", ".join(f"`{c}`" for c in columns)
    for row in rows:
        values = ", ".join(sql_value(row[c]) for c in columns)
        lines.append(f"INSERT INTO `{args.table}` ({col_list}) VALUES ({values});")

    lines.append("")
    lines.append(f"SELECT COUNT(*) AS rows_loaded FROM `{args.table}`;")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
