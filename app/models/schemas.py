from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: int
    #Field(...) makes it mandatory. max Field keeps the length limited to 500
    query: str= Field(...,max_length=500)
