from typing import Optional, List
from .base import AIProvider, SummaryResult
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from ..config import settings
from ..models import AIProvider as AIProviderEnum
import random
import asyncio

class AIProviderManager:
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        # Initialize OpenAI providers
        if settings.openai_api_key:
            self.providers[AIProviderEnum.OPENAI_GPT4] = OpenAIProvider(
                settings.openai_api_key, "gpt-4"
            )
            self.providers[AIProviderEnum.OPENAI_GPT35] = OpenAIProvider(
                settings.openai_api_key, "gpt-3.5-turbo"
            )
        
        # Initialize Anthropic provider
        if settings.anthropic_api_key:
            self.providers[AIProviderEnum.ANTHROPIC_CLAUDE] = AnthropicProvider(
                settings.anthropic_api_key
            )
        
        # Initialize Google provider
        if settings.google_api_key:
            self.providers[AIProviderEnum.GOOGLE_GEMINI] = GoogleProvider(
                settings.google_api_key
            )
    
    def get_provider(self, provider_type: AIProviderEnum) -> Optional[AIProvider]:
        return self.providers.get(provider_type)
    
    def get_available_providers(self) -> List[AIProviderEnum]:
        available = []
        for provider_type, provider in self.providers.items():
            if provider.is_available():
                available.append(provider_type)
        return available
    
    async def summarize_with_fallback(
        self,
        text: str,
        primary_provider: AIProviderEnum,
        fallback_provider: Optional[AIProviderEnum] = None,
        max_length: int = 500,
        demo_mode: bool = False
    ) -> SummaryResult:
        
        # Demo mode simulation
        if demo_mode:
            return await self._demo_summarize(text, primary_provider)
        
        # Try primary provider
        primary = self.get_provider(primary_provider)
        if primary and primary.is_available():
            try:
                return await primary.summarize(text, max_length)
            except Exception as e:
                print(f"Primary provider {primary_provider} failed: {e}")
        
        # Try fallback provider
        if fallback_provider:
            fallback = self.get_provider(fallback_provider)
            if fallback and fallback.is_available():
                try:
                    return await fallback.summarize(text, max_length)
                except Exception as e:
                    print(f"Fallback provider {fallback_provider} failed: {e}")
        
        # Try any available provider
        available = self.get_available_providers()
        for provider_type in available:
            if provider_type not in [primary_provider, fallback_provider]:
                provider = self.get_provider(provider_type)
                try:
                    return await provider.summarize(text, max_length)
                except Exception as e:
                    print(f"Provider {provider_type} failed: {e}")
        
        raise Exception("All AI providers failed or unavailable")
    
    async def _demo_summarize(self, text: str, provider: AIProviderEnum) -> SummaryResult:
        # Simulate processing delay
        delay = random.uniform(1, 5)
        await asyncio.sleep(delay)
        
        # Simulate random failure
        if random.random() < settings.demo_failure_rate:
            raise Exception("Demo mode: Simulated provider failure")
        
        # Generate demo summary
        words = text.split()[:100]
        summary = f"This is a demo summary of a document containing {len(text)} characters. " \
                 f"The document appears to discuss: {' '.join(words[:20])}..."
        
        key_points = [
            "Demo key point 1: Document processing successful",
            "Demo key point 2: AI provider simulation active",
            f"Demo key point 3: Processed {len(text)} characters",
            "Demo key point 4: Cost estimation available",
            "Demo key point 5: Fallback mechanism ready"
        ]
        
        entities = [
            {"type": "organization", "value": "Demo Corp"},
            {"type": "date", "value": "2024-01-15"},
            {"type": "person", "value": "John Demo"},
            {"type": "location", "value": "Demo City"},
            {"type": "money", "value": "$1,234.56"}
        ]
        
        # Estimate tokens and cost
        tokens = len(text) // 4
        cost = tokens * 0.001  # $0.001 per token for demo
        
        return SummaryResult(
            summary=summary,
            key_points=key_points,
            entities=entities,
            tokens_used=tokens,
            cost=cost,
            provider_used=f"Demo/{provider.value}"
        )
    
    def estimate_cost(self, text: str, provider: AIProviderEnum) -> float:
        p = self.get_provider(provider)
        if p:
            tokens = p.estimate_tokens(text)
            # Assume output is ~20% of input
            output_tokens = tokens // 5
            return p.estimate_cost(tokens, output_tokens)
        return 0.0