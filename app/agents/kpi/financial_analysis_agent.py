"""Financial analysis agent for KPI extraction."""

import logging
import json
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from app.config.settings import config
from app.config.kpi_schema import KPIMetrics

logger = logging.getLogger(__name__)


class FinancialAnalysisAgent:
    """Extracts BFSI KPIs from document chunks."""
    
    def __init__(self):
        """Initialize financial analysis agent."""
        self.llm = self._get_llm()
        self.output_parser = PydanticOutputParser(pydantic_object=KPIMetrics)
    
    def _get_llm(self):
        """Get LLM instance based on configuration."""
        provider = config.llm.provider
        
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.llm.model,
                temperature=config.llm.temperature,
                api_key=config.llm.api_key
            )
        elif provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=config.llm.model,
                    temperature=config.llm.temperature,
                    api_key=config.llm.api_key
                )
            except ImportError:
                raise ImportError("langchain-anthropic not installed. Install with: pip install langchain-anthropic")
        elif provider == "azure":
            from langchain_openai import AzureChatOpenAI
            return AzureChatOpenAI(
                deployment_name=config.llm.deployment_name,
                model=config.llm.model,
                temperature=config.llm.temperature,
                api_key=config.llm.api_key,
                azure_endpoint=config.llm.endpoint,
                api_version=config.llm.api_version
            )
        elif provider == "custom":
            # For custom endpoints, use OpenAI-compatible interface
            from langchain_openai import ChatOpenAI
            from app.utils.llm_optimizations import apply_llm_optimizations
            
            llm = ChatOpenAI(
                model=config.llm.model,
                temperature=config.llm.temperature,
                base_url=config.llm.endpoint,
                api_key=config.llm.api_key or "dummy"
            )
            
            # Apply optimizations (KV-caching, speculative decoding)
            return apply_llm_optimizations(llm)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def extract_kpis(self, chunks: List[Document]) -> Dict[str, Any]:
        """Extract BFSI KPIs from document chunks.
        
        Args:
            chunks: List of relevant Document objects
            
        Returns:
            Dictionary with KPI data (using 'not_found' for missing values)
        """
        if not chunks:
            logger.warning("No chunks provided for KPI extraction")
            return KPIMetrics().to_dict()
        
        try:
            # Combine chunk texts
            context = "\n\n".join([
                f"Chunk {i+1} (Page {chunk.metadata.get('page', 'N/A')}):\n{chunk.page_content}"
                for i, chunk in enumerate(chunks)
            ])
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a financial analysis expert specializing in BFSI (Banking, Financial Services, and Insurance) documents.

Your task is to extract key financial metrics and KPIs from the provided document chunks. Extract the following metrics:

**Financial Metrics:**
- Revenue (total revenue, income)
- Net Profit (profit after tax, PAT)
- ROE (Return on Equity) as percentage
- ROA (Return on Assets) as percentage

**Asset Quality Metrics:**
- GNPA (Gross Non-Performing Assets) as percentage
- NNPA (Net Non-Performing Assets) as percentage
- PCR (Provision Coverage Ratio) as percentage

**Capital Adequacy:**
- CRAR (Capital to Risk-Weighted Assets Ratio) as percentage
- CAR (Capital Adequacy Ratio) as percentage

**Growth Metrics:**
- Revenue growth QoQ (Quarter over Quarter) as percentage
- Revenue growth YoY (Year over Year) as percentage
- Profit growth QoQ as percentage
- Profit growth YoY as percentage

**Additional Information:**
- Currency unit (e.g., INR, USD)
- Reporting period (e.g., Q1 FY2024, Annual 2023)

**Important:**
- Extract exact numerical values from the document
- If a metric is not found, use "not_found" as the value
- Preserve the currency and period information if available
- Be precise with percentages and decimal values

{format_instructions}"""),
                ("human", "Extract KPIs from the following document chunks:\n\n{context}")
            ])
            
            # Format prompt with instructions
            formatted_prompt = prompt.format_messages(
                context=context,
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Get LLM response
            response = self.llm.invoke(formatted_prompt)
            
            # Parse response
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Try to parse as JSON first, then as Pydantic
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                elif "```" in content:
                    json_start = content.find("```") + 3
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                
                kpi_dict = json.loads(content)
                kpi_metrics = KPIMetrics.from_dict(kpi_dict)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse structured output, using fallback: {str(e)}")
                # Fallback: use output parser directly
                kpi_metrics = self.output_parser.parse(content)
            
            result = kpi_metrics.to_dict()
            logger.info(f"Extracted KPIs: {sum(1 for v in result.values() if v != 'not_found')} metrics found")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting KPIs: {str(e)}")
            # Return empty KPIs with all 'not_found'
            return KPIMetrics().to_dict()
