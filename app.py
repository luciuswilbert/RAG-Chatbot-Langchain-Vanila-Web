'''
IN ORDER TO RUN THIS FILE WITHOUT CHAINLIT:
1. UNCOMMENT THE if __name__ == "__main__" CODE 
2. Command = python app.py
'''

from flask import Flask, render_template, request, jsonify
import os
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.schema import SystemMessage, HumanMessage, Document

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# Global variable to store the FAISS index
faiss_db = None

def get_azure_embeddings():
    """
    Initialize Azure OpenAI embeddings
    """
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    embedding_deployment = os.getenv("EMBEDDING_DEPLOYMENT_NAME")
    embedding_model = os.getenv("EMBEDDING_MODEL_NAME")
    api_version = os.getenv("API_VERSION")
    
    return AzureOpenAIEmbeddings(
        azure_deployment=embedding_deployment,
        openai_api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
        chunk_size=1
    )

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text

def chunk_text(text, chunk_size=300, overlap=50):
    """
    Splits text into chunks with optional overlap.
    """
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def query_faiss(faiss_db, query, k=4):
    results = faiss_db.similarity_search(query, k=k)
    return results

def generate_llm_answer_langchain(context, user_query):
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("DEPLOYMENT_NAME")
    api_version = os.getenv("API_VERSION")
    llm = AzureChatOpenAI(
        azure_endpoint=azure_endpoint,
        openai_api_key=azure_api_key,
        deployment_name=azure_deployment,
        api_version=api_version,
        temperature=0.1,
        streaming=False
    )
    system = SystemMessage(content="You are AI Assistant. Provide clear, accurate, and concise answers strictly based on the context provided. Ensure your responses are balanced in length—neither too brief nor overly detailed—delivering essential information effectively and efficiently. Avoid including any information not supported by the given context.")
    user = HumanMessage(content=f"Context:\n{context}\n\nUser Question: {user_query}\n\nAnswer using only the given context.")
    response = llm.invoke([system, user])
    return response.content.strip()

# --- FLASK ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    global faiss_db
    file = request.files.get('pdf')
    if not file or not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'Please upload a PDF file.'}), 400
    # Save uploaded PDF
    upload_path = os.path.join('uploads', file.filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(upload_path)
    # Extract text and build FAISS
    try:
        extracted_text = extract_text_from_pdf(upload_path)
        chunks = chunk_text(extracted_text)
        embedding_fn = get_azure_embeddings()
        documents = [Document(page_content=chunk) for chunk in chunks]
        faiss_db = FAISS.from_documents(
            documents=documents,
            embedding=embedding_fn
        )
        faiss_db.save_local("my_faiss_index")
        return jsonify({'success': True, 'message': 'PDF uploaded and knowledge base created.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    global faiss_db
    data = request.get_json()
    user_message = data.get('message', '')
    if faiss_db is None:
        # Try to load existing index
        if os.path.exists("my_faiss_index"):
            embedding_fn = get_azure_embeddings()
            faiss_db = FAISS.load_local(
                "my_faiss_index",
                embeddings=embedding_fn,
                allow_dangerous_deserialization=True
            )
        else:
            return jsonify({'success': False, 'error': 'No knowledge base available. Please upload a PDF first.'}), 400
    try:
        results = query_faiss(faiss_db, user_message, k=4)
        context = "\n\n".join([doc.page_content for doc in results])
        answer = generate_llm_answer_langchain(context, user_message)
        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

# if __name__ == "__main__":
#     pdf_path = "Resume - Lucius Wilbert Tjoa.pdf"  
#     extracted_text = extract_text_from_pdf(pdf_path)
#     chunks = chunk_text(extracted_text)

#     embedding_fn = LMStudioEmbeddings()

#     documents = [Document(page_content=chunk) for chunk in chunks]

#     faiss_db = FAISS.from_documents(
#         documents=documents,
#         embedding=embedding_fn
#     )

#     faiss_db.save_local("my_faiss_index")
#     user_query = input("Enter your question: ")
#     results = query_faiss("my_faiss_index", user_query)

#     context = "\n\n".join([doc.page_content for doc in results])
#     prompt = (
#         f"Context:\n{context}\n\n"
#         f"User Question: {user_query}\n\n"
#         "Answer using only the given context."
#     )

#     llm_answer = generate_llm_answer_langchain(context, user_query)
#     print("\nLLM Answer:\n", llm_answer)



