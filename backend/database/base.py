from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseDatabase(ABC):
    @abstractmethod
    def execute(self, sql: str) -> Dict[str, Any]:
        """
        Executes a SQL query.
        
        Args:
            sql (str): The raw SQL query to execute.
            
        Returns:
            Dict[str, Any]: A dictionary containing execution status, 
                            row count, and the fetched data.
        """
        pass