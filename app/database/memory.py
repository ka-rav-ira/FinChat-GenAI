import os 
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine,Column,Integer,String,Text,DateTime
from sqlalchemy.orm import declarative_base,sessionmaker


#Locate the project root and lead the .env file
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(os.path.join(BASE_DIR,".env"))


# Enterprise Database Connection URL
DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environmemt or .env file!")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#Define the Memory Schema with an index on session_id for O(log N) lookuos
class ChatMessage(Base):
    __tablename__ = "chat_history"

    id = Column(Integer,primary_key=True, index = True)
    session_id = Column(String(50),index=True,nullable=False)
    role = Column(String(20),nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

#Create the table in Postgresql if it doesn't exist
Base.metadata.create_all(bind=engine)


#Helper function to interface with FastAPI and LangChain
def add_message(session_id: str, role: str, content: str):
    """Saves a single message to the persistent Postgres ledger."""
    db = SessionLocal()
    try:
        new_msg = ChatMessage(session_id=session_id,role=role,content=content)
        db.add(new_msg)
        db.commit()
    finally:
        db.close()

def get_chat_history(session_id: str, limit: int = 10):
    """Retrieves the last N messages for the LangChain context window."""
    db = SessionLocal()
    try:
        messages = db.query(ChatMessage)\
        .filter(ChatMessage.session_id == session_id)\
        .order_by(ChatMessage.created_at.asc())\
        .limit(limit)\
        .all()

        #Format for LangChain consumption
        formatted_history = []
        for msg in messages:
            formatted_history.append((msg.role, msg.content))
        return formatted_history
    finally:
        db.close()

if __name__ == "__main__":
#Quick connection test
    print("Testing PostgreSQL connection via .env...")
    add_message("test_session_001","user","Hello, is the database connected via env?")
    history = get_chat_history("test_session_001")
    print(f"Success! Retrieved from Postgres: {history}")
