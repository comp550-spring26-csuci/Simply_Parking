from database_manager import DatabaseManager

def main():
    with DatabaseManager() as db:
        rows = db.fetch_all(limit=50)  # change limit or set None for all

    for (id_, plate, source_file, ts) in rows:
        print(f"{id_:>5}  {plate:<10}  {ts}  {source_file}")

if __name__ == "__main__":
    main()

