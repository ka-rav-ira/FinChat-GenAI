from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: int
    #Field(...) makes it mandatory. max Field keeps the length limited to 500
    query: str= Field(...,max_length=500)

#New: GuardRail for uploading new financial policies into ChromaDB
class DocumentIngestRequest(BaseModel):
    user_id:int
    doc_id: str
    content: str
    category: str
    bank: str