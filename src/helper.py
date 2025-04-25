from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_openai import OpenAIEmbeddings
# from langchain_community.embeddings import HuggingFaceEmbeddings

#Extract Data from the PDF File

def load_pdf_file(data):
    loader = DirectoryLoader(data,
                             glob="*.pdf",
                             loader_cls=PyPDFLoader)
    
    documents=loader.load()

    return documents

#Split the data into text chunks

def text_split(extracted_data):
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    text_chunks = text_splitter.split_documents(extracted_data)

    return text_chunks

#Download HuggingFace

# def download_hugging_face_embeddings():
#     embeddings=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
#     return embeddings

# Download OpenAI Embeddings
def download_openai_embeddings():  # ✅ Renamed for clarity
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    return embeddings