from flask import Flask , render_template,jsonify,request
# from src.helper import download_hugging_face_embeddings
from src.helper import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
# from langchain_openai import OpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from src.prompt import *
import os
import re
from collections import OrderedDict,defaultdict

app = Flask(__name__)

load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# embeddings = download_hugging_face_embeddings()
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

index_name = "ktc-bot"

docsearch = PineconeVectorStore.from_existing_index(
    index_name = index_name,
    embedding=embeddings,
)

retriever = docsearch.as_retriever(search_type="similarity" , search_kwargs={"k" :5})

# llm = OpenAI(temperature = 0.4 , max_tokens= 1500)

llm = ChatOpenAI(
    model="gpt-3.5-turbo",  
    temperature=0.4,
    max_tokens=1500
)

# Create a ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

question_answer_chain = create_stuff_documents_chain(llm,prompt)
rag_chain = create_retrieval_chain(retriever,question_answer_chain)

@app.route("/")
def index():
    return render_template('chat.html')

# @app.route("/get" , methods=["GET","POST"])
# def chat():
#     msg = request.form["msg"]
#     input = msg
#     print(input)
#     response = rag_chain.invoke({"input": msg})
#     print("Response : ", response["answer"])
#     return str (response ["answer"])

@app.route("/get", methods=["GET", "POST"])
def chat():
    msg = request.form["msg"]
    print(f"🧠 User Input: {msg}")

    # Step 1: Get the model's response
    response = rag_chain.invoke({"input": msg})
    answer = response["answer"]
    context_docs = response.get("context", [])

    reference_map = OrderedDict()
    ref_pages_map = defaultdict(set)  # filename → set of pages
    ref_counter = 1

    for doc in context_docs:
        title = doc.metadata.get("title", None)
        source = os.path.basename(doc.metadata.get("source", "Unknown.pdf"))
        page = int(doc.metadata.get("page", 0)) + 1  # adjust to human-readable

        # Clean display
        if title and title != source:
            ref_text = f"{title} – {source}"
        else:
            ref_text = f"{source}"

        # First time we see this reference
        if ref_text not in reference_map:
            reference_map[ref_text] = ref_counter
            ref_counter += 1

        # Add the page number to this document's set
        ref_pages_map[ref_text].add(page)

    # Only include references that were used
    used_refs = set(re.findall(r"\[(\d+)\]", answer))
    final_refs = {
        ref: num for ref, num in reference_map.items()
        if str(num) in used_refs
    }

    # Format reference section with page ranges
    formatted_refs = "<br>".join([
        f"{num}. {ref} – (Page{'s' if len(ref_pages_map[ref]) > 1 else ''} {', '.join(map(str, sorted(ref_pages_map[ref])))})"
        for ref, num in final_refs.items()
    ])

    final_output = answer + f"<br><br><b>References:</b><br>{formatted_refs}"

    return final_output

if __name__ == '__main__':
        app.run(host="0.0.0.0" , port = 8080 , debug = True)

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

        