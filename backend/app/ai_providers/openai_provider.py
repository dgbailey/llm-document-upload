import openai
from typing import List, Dict
from .base import AIProvider, SummaryResult
import tiktoken
import asyncio
from ..config import settings

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model_name)
        self.client = openai.AsyncOpenAI(api_key=api_key) if api_key else None
        
        if model_name == "gpt-4":
            self.input_cost_per_1k = settings.openai_gpt4_input_cost
            self.output_cost_per_1k = settings.openai_gpt4_output_cost
        else:
            self.input_cost_per_1k = settings.openai_gpt35_input_cost
            self.output_cost_per_1k = settings.openai_gpt35_output_cost
    
    async def summarize(self, text: str, max_length: int = 500) -> SummaryResult:
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        try:
            # Prepare the prompt
            prompt = f"""Please provide a comprehensive summary of the following document in approximately {max_length} words.
            Also extract:
            1. Key points (as bullet points)
            2. Important entities (people, organizations, dates, etc.)
            
            Document:
            {text[:8000]}  # Limit input to avoid token limits
            
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
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful document summarization assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            # Parse response
            summary = ""
            key_points = []
            entities = []
            
            if "SUMMARY:" in content:
                summary = content.split("SUMMARY:")[1].split("KEY POINTS:")[0].strip()
            
            key_points = self.extract_key_points(content)
            entities = self.extract_entities(text)
            
            # Calculate tokens and cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = input_tokens + output_tokens
            cost = self.estimate_cost(input_tokens, output_tokens)
            
            return SummaryResult(
                summary=summary,
                key_points=key_points,
                entities=entities,
                tokens_used=total_tokens,
                cost=cost,
                provider_used=f"OpenAI/{self.model_name}"
            )
            
        except Exception as e:
            raise Exception(f"OpenAI summarization failed: {str(e)}")
    
    def estimate_tokens(self, text: str) -> int:
        try:
            encoding = tiktoken.encoding_for_model(self.model_name)
            return len(encoding.encode(text))
        except:
            # Fallback estimation: ~4 chars per token
            return len(text) // 4
    
    def is_available(self) -> bool:
        return self.client is not None