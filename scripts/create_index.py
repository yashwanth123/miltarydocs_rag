from dotenv import load_dotenv

from backend.vector_store.chroma_client import collection_count, reset_collection

load_dotenv()


def main() -> None:
    print("Resetting local ChromaDB collection...")
    reset_collection()
    print(f"Ready. Current chunk count: {collection_count()}")


if __name__ == "__main__":
    main()
