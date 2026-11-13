from fastapi import APIRouter,Path,HTTPException,UploadFile,File,Form
from app.models.schemas import ChatRequest, DocumentIngestRequest
import ollama
import google.generativeai as genai
import os 
from dotenv import load_dotenv
from pathlib import Path
#import asyncio native python library for handling the time delays
import asyncio
from app.database.vector_store import search_documents, add_document,ingest_chunked_document
from pypdf import PdfReader
import io


# Find the project root (GENAI_Backend) from any subdirectory
BASE_DIR = Path(__file__).resolve().parent  # Adjust .parent level depending on file depth
load_dotenv(BASE_DIR / ".env")
#This intializes the API Application 
router = APIRouter()


#The Endpoint: Using the Guardrail (request:chatRequest)
@router.post("/chat/{session_id}")
async def process_chat(

  request:ChatRequest,
  session_id:str = Path(...,title="The id of the chat session"),
  model: str = "llama3"
): 


    #Search ChromaDB using the user's question
    search_results = search_documents(query=request.query,top_results=1)


    #Unpack the text from the double brackets
    if search_results["documents"] and search_results["documents"][0]:
        retrieved_context = search_results["documents"][0][0]
    else:
        retrieved_context="No internal policy found."

    rag_prompt = f"""You are Finchat, a strict Financial Operations Assistant.
    Answer the user's question using ONLY the internal policy below.
    If the answer is not in the policy, say: "I cannot verify this from internal settlement documentation."
    
    INTERNAL POLICY:
    {retrieved_context}

    USER QUESTION:
    {request.query}"""
    
    #######################
    #BUSINESS LOGIC LAYER#
    #######################

    #3Security Check
    #If someone tries to access: "Admin Chat" but he don't have the access for the same
    if session_id == "admin_chat" and request.user_id!=0:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You don't have access to admin chat."
        )

    #Check which engine is active in this .env file(defaults to ollama)
    engine = os.getenv("ACTIVE_AI_ENGINE","ollama").lower()
    try:
        if engine == "ollama":
            # Engine 1 :- Local System Hardware(Zero Data leak)
            ai_response = await ollama.AsyncClient().chat(
                model=model, # ✅ Added the missing comma here
                messages=[{'role':'user','content':rag_prompt}]
            )
            # ✅ Indented this 4 spaces to the right so it stays inside the 'if' block
            bot_response = ai_response['message']['content']

        elif engine == "cloud":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Missing Gemini API Key in .env file")

            genai.configure(api_key=api_key)
            cloud_model = genai.GenerativeModel('gemini-3.8-flash')

            response = cloud_model.generate_content(rag_prompt)
            bot_response = response.text

        else:
            raise ValueError(f"Invalid AI Engine configured: {engine}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

    
    return{
        "status":"Success",
        "session": session_id,
        "ai_model_used":model,
        "user": request.user_id,
        "bot_reply":bot_response,
        "source_context":retrieved_context
    }


@router.post("/ingest")
async def ingest_document(request: DocumentIngestRequest):

    # 1. RBAC Security Gate: Only Admins (user_id == 0) can upload policies
    if request.user_id != 0:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only administrators (user_id 0) can ingest new policies."
        )

    # 2. Pack category and bank into a metadata dictionary for ChromaDB
    policy_metadata = {
        "category": request.category,
        "bank": request.bank
    }

    # 3. Call your vector_store function to embed and save the policy
    add_document(
        doc_id=request.doc_id,
        content=request.content,
        metadata=policy_metadata
    )

    return {
        "status": "Success",
        "message": f"Document '{request.doc_id}' successfully added to ChromaDB.",
        "metadata": policy_metadata
    }


@router.post("/ingest-pdf")
async def ingest_pdf_document(
    user_id: int = Form(...),
    doc_id: str = Form(...),
    category: str = Form(...),
    bank: str = Form(...),
    file: UploadFile = File(...)
):
    if user_id!=0:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only administrators (user_id 0) can upload compliance PDFs."
        )

    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only .pdf files are supported."
        )

    try:
        pdf_bytes = await file.read()
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))

        extracted_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text + "\n\n"

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could Not extract any readable text from the uploaded PDF."
            )

        policy_metadata = {
            "category": category,
            "bank": bank,
            "source_file": file.filename
        }

        total_chunks = ingest_chunked_document(
            doc_id = doc_id,
            full_text=extracted_text,
            metadata=policy_metadata
        )

        return {
            "status": "Success",
            "filename": file.filename,
            "pages_processed": len(pdf_reader.pages),
            "chunks_stored": total_chunks,
            "metadata": policy_metadata
        }


    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF ingestion Error: {str(e)}")