import anthropic
from typing import List, Dict
from .base import AIProvider, SummaryResult
from ..config import settings

class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str = "claude-3-sonnet-20240229"):
        super().__init__(api_key, model_name)
        self.client = anthropic.AsyncAnthropic(api_key=api_key) if api_key else None
        self.input_cost_per_1k = settings.anthropic_claude_input_cost
        self.output_cost_per_1k = settings.anthropic_claude_output_cost
    
    async def summarize(self, text: str, max_length: int = 500) -> SummaryResult:
        if not self.client:
            raise ValueError("Anthropic API key not configured")
        
        try:
            prompt = f"""Please provide a comprehensive summary of the following document in approximately {max_length} words.
            Also extract:
            1. Key points (as bullet points)
            2. Important entities (people, organizations, dates, etc.)
            
            Document:
            {text[:8000]}  # Limit input
            
            Format your response as:
            SUMMARY:
            [Your summary here]
            
            KEY POINTS:
            • [Point 1]
            • [Point 2]
            • [Point 3]
            
            ENTITIES:
            - [Entity 1: Type]
            - [Entity 2: Type]
            """
            
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            
            # Parse response
            summary = ""
            if "SUMMARY:" in content:
                summary = content.split("SUMMARY:")[1].split("KEY POINTS:")[0].strip()
            
            key_points = self.extract_key_points(content)
            entities = self.extract_entities(text)
            
            # Estimate tokens (Anthropic doesn't provide exact usage)
            input_tokens = self.estimate_tokens(text)
            output_tokens = self.estimate_tokens(content)
            total_tokens = input_tokens + output_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)
            
            return SummaryResult(
                summary=summary,
                key_points=key_points,
                entities=entities,
                tokens_used=total_tokens,
                cost=cost,
                provider_used=f"Anthropic/{self.model_name}"
            )
            
        except Exception as e:
            raise Exception(f"Anthropic summarization failed: {str(e)}")
    
    def estimate_tokens(self, text: str) -> int:
        # Rough estimation for Claude
        return len(text) // 4
    
    def is_available(self) -> bool:
        return self.client is not None