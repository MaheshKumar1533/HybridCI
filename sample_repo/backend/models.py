"""
Database models
"""
from dataclasses import dataclass

@dataclass
class User:
    """User model."""
    __tablename__ = 'users'
    
    id: int
    username: str
    email: str
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }
    
    @classmethod
    def query(cls):
        return QueryBuilder(cls)

class QueryBuilder:
    def __init__(self, model):
        self.model = model
    
    def all(self):
        return []
    
    def get(self, id):
        return None
