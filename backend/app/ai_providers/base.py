from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class SummaryResult:
    summary: str
    key_points: List[str]
    entities: List[Dict[str, str]]
    tokens_used: int
    cost: float
    provider_used: str

class AIProvider(ABC):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.input_cost_per_1k = 0.0
        self.output_cost_per_1k = 0.0
    
    @abstractmethod
    async def summarize(self, text: str, max_length: int = 500) -> SummaryResult:
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        pass
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k
        return input_cost + output_cost
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    def extract_key_points(self, text: str) -> List[str]:
        lines = text.split('\n')
        key_points = []
        for line in lines:
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                key_points.append(line.lstrip('•-* '))
        return key_points[:5]  # Top 5 key points
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        entities = []
        # Simple entity extraction (can be enhanced with NER)
        import re
        
        # Extract emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({"type": "email", "value": email})
        
        # Extract URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        for url in urls:
            entities.append({"type": "url", "value": url})
        
        # Extract dates (simple pattern)
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)
        for date in dates:
            entities.append({"type": "date", "value": date})
        
        # Extract monetary amounts
        amounts = re.findall(r'\$[\d,]+\.?\d*', text)
        for amount in amounts:
            entities.append({"type": "money", "value": amount})
        
        return entities[:10]  # Limit to 10 entities