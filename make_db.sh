# Usage: source make_db.sh <path to database file> <path to csv>

rm $1
sqlite3 $1 < query-create-database.sql
python3 populate_db.py $2 | sqlite3 $1