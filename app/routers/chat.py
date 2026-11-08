from fastapi import APIRouter,Path,HTTPException
from app.models.schemas import ChatRequest 
import ollama
import google.generativeai as genai
import os 
from dotenv import load_dotenv
#import asyncio native python library for handling the time delays
import asyncio


load_dotenv()

#This intializes the API Application 
router = APIRouter()


#The Endpoint: Using the Guardrail (request:chatRequest)
@router.post("/chat/{session_id}")
async def process_chat(
  request:ChatRequest,
  session_id:str = Path(...,title="The id of the chat session"),
  model: str = "llama3"
): 

    
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
                messages=[{'role':'user','content':request.query}]
            )
            # ✅ Indented this 4 spaces to the right so it stays inside the 'if' block
            bot_response = ai_response['message']['content']

        elif engine == "cloud":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Missing Gemini API Key in .env file")

            genai.configure(api_key=api_key)
            cloud_model = genai.GenerativeModel('gemini-1.5-flash')

            response = cloud_model.generate_content(request.query)
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
        "bot_reply":bot_response
    }