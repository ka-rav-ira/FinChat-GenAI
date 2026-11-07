from fastapi import FastAPI,Path,HTTPException
from pydantic import BaseModel, Field
#import asyncio native python library for handling the time delays
import asyncio



#This intializes the API Application 
app = FastAPI()

#The GuardRail : Strict DTO Object


# NEW: This fixes your "Normal URL" issue!
@app.get("/")
async def home():
    return {"message": "Finchat server is running!"}

class chatRequest(BaseModel):
    user_id: int
    #Field(...) makes it mandatory. max Field keeps the length limited to 500
    query: str= Field(...,max_length=500)




#The Endpoint: Using the Guardrail (request:chatRequest)
@app.post("/chat/{session_id}")
async def process_chat(
  request:chatRequest,
  session_id:str = Path(...,title="The id of the chat session"),
  model: str = "gemini-flash"
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

    await asyncio.sleep(3)
    bot_response = f"Simulated AI Answer for: {request.query}"

    
    return{
        "status":"Success",
        "session": session_id,
        "ai_model_used":model,
        "user": request.user_id,
        "bot_reply":bot_response
    }