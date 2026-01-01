import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.bot.documents.store import DocumentStore  # noqa: E402


def test_persistence():
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "test_docs.json"

        # 1. Create store and add persistent record
        print("1. Creating store and adding record...")
        store1 = DocumentStore(storage_path=str(db_path))
        record = store1.add_document("test.txt", 12345)
        print(f"   Added record: {record.id}")

        # 2. Modify record
        print("2. Modifying record...")
        store1.set_index_state(record.id, True, chunks=5)

        # 3. Create NEW store instance pointing to same file
        print("3. Reloading from disk...")
        store2 = DocumentStore(storage_path=str(db_path))
        loaded_record = store2.get_document(record.id)

        # 4. Verify
        print("4. Verifying...")
        if not loaded_record:
            print("❌ Record not found in reloaded store!")
            sys.exit(1)

        if loaded_record.name != "test.txt":
            print(f"❌ Name mismatch: {loaded_record.name}")
            sys.exit(1)

        if not loaded_record.indexed:
            print("❌ Indexed state not persisted!")
            sys.exit(1)

        if loaded_record.chunks != 5:
            print(f"❌ Chunks mismatch: {loaded_record.chunks}")
            sys.exit(1)

        print("✅ Persistence test passed!")


if __name__ == "__main__":
    test_persistence()
