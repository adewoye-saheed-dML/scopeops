from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Category(Base):
    __tablename__ = "categories"
    
    category_id: Mapped[str] = mapped_column(String, primary_key=True)
    category_name: Mapped[str] = mapped_column(String, nullable=False)
    parent_category_id: Mapped[str] = mapped_column(String, nullable=True)
