
# from src.helper import load_pdf_file, text_split, download_hugging_face_embeddings
from src.helper import load_pdf_file, text_split, OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain.docstore.document import Document
from dotenv import load_dotenv
import os
import hashlib
import time

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "ktc-bot"

# Create the index if it doesn't already exist
if index_name not in [index.name for index in pc.list_indexes()]:
    pc.create_index(
        name=index_name,
        dimension=1536,  # for OpenAI embeddings
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

# Helper: create a consistent hash from text
def get_text_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

# Helper: get existing vector IDs from Pinecone
def get_existing_ids(index, ids_to_check, max_ids_per_batch=50):
    existing_ids = set()
    for i in range(0, len(ids_to_check), max_ids_per_batch):
        batch = ids_to_check[i:i + max_ids_per_batch]
        try:
            fetched = index.fetch(ids=batch)
            existing_ids.update(fetched.vectors.keys())
        except Exception as e:
            print(f"❌ Error during fetch batch {i//max_ids_per_batch + 1}: {e}")
    return existing_ids

# Helper: attempt to extract a short title/section line from the content
def auto_extract_section(text, max_length=80):
    lines = text.strip().split('\n')
    for line in lines:
        if 10 < len(line.strip()) < max_length:
            return line.strip()
    return "General Content"

# Init
index = pc.Index(index_name)
embeddings = OpenAIEmbeddings()

# Main loop
while True:
    print("\n🔄 Loading and splitting PDF...")
    extracted_data = load_pdf_file(data='Data/')
    text_chunks = text_split(extracted_data)

    print("🔐 Generating IDs for chunks...")
    all_ids = [get_text_hash(doc.page_content) for doc in text_chunks]

    print("🔍 Checking for existing documents in Pinecone...")
    existing_ids = get_existing_ids(index, all_ids)
    print(f"📦 Found {len(existing_ids)} existing IDs.")

    new_chunks = []
    for doc in text_chunks:
        doc_id = get_text_hash(doc.page_content)
        if doc_id not in existing_ids:
            doc.metadata["id"] = doc_id

            # 📁 Extract PDF filename from path
            source_path = doc.metadata.get("source", "unknown.pdf")
            filename = os.path.basename(source_path).replace(".pdf", "")
            doc.metadata["source"] = filename

            # 🧠 Auto-detect section title from content
            doc.metadata["section"] = auto_extract_section(doc.page_content)

            # 📄 Page number if available (e.g., from PyPDFLoader)
            doc.metadata["page"] = doc.metadata.get("page", "unknown")

            new_chunks.append(doc)

    if not new_chunks:
        print("✅ No new documents to upload. Finished.")
        break

    print(f"🚀 Uploading {len(new_chunks)} new documents...")

    docs_with_ids = [(doc, doc.metadata["id"]) for doc in new_chunks]

    docsearch = PineconeVectorStore.from_documents(
        documents=[doc for doc, _id in docs_with_ids],
        embedding=embeddings,
        index_name=index_name,
        ids=[_id for doc, _id in docs_with_ids]
    )

    print("✅ Upload complete. Waiting before next check...")
    time.sleep(2)
