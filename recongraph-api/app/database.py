from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import Column, String, Integer, DateTime, Float
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./hitl_feedback.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
        
    tenant_id = Column(String, index=True, nullable=False, default="default")

Base = declarative_base(cls=Base)

# Example Table for phase 8
class Feedback(Base):
    __tablename__ = "feedback_v2"
    
    review_id = Column(Integer, primary_key=True, index=True)
    packet_id = Column(String, index=True)
    purchase_record_id = Column(String)
    gst_record_id = Column(String)
    deterministic_decision = Column(String)
    deterministic_score = Column(Float)
    deterministic_coverage = Column(Float)
    ml_score = Column(Float)
    calibrated_ml_probability = Column(Float)
    graph_features = Column(String)
    evidence_features = Column(String)
    final_human_decision = Column(String)
    reviewer_action = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    engine_version = Column(String)
    model_version = Column(String)
    config_hash = Column(String)
    explanation_version = Column(String)
    rag_context_identifiers = Column(String)
    legacy_payload = Column(String)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
