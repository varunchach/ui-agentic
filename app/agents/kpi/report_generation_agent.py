"""Report generation agent for KPI reports."""

import logging
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate

from app.config.settings import config

logger = logging.getLogger(__name__)


class ReportGenerationAgent:
    """Generates structured BFSI reports from KPI data."""
    
    def __init__(self):
        """Initialize report generation agent."""
        self.llm = self._get_llm()
    
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
    
    def generate_report(self, kpi_data: Dict[str, Any]) -> str:
        """Generate structured BFSI report from KPI data.
        
        Args:
            kpi_data: Dictionary with KPI metrics
            
        Returns:
            Markdown-formatted report
        """
        try:
            # Format KPI data for prompt
            kpi_summary = self._format_kpi_data(kpi_data)
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a senior financial analyst specializing in BFSI sector reports.

Generate a comprehensive, professional BFSI report based on the extracted KPI data. The report should be well-structured, insightful, and suitable for executive review.

**Report Structure:**

1. **Executive Summary**
   - Brief overview of key findings
   - Highlight most important metrics
   - Overall financial health assessment

2. **Key Financial Highlights**
   - Revenue and profitability analysis
   - ROE and ROA performance
   - Growth trends (QoQ/YoY if available)
   - Currency and period context

3. **Risk & Asset Quality**
   - GNPA and NNPA analysis
   - Provision Coverage Ratio (PCR) assessment
   - Asset quality trends and implications

4. **Capital Adequacy**
   - CRAR/CAR analysis
   - Regulatory compliance status
   - Capital strength assessment

5. **Trends & Red Flags**
   - Notable trends (positive or negative)
   - Potential concerns or risks
   - Recommendations or observations

**Guidelines:**
- Use professional, analytical language
- Include specific numbers and percentages where available
- Clearly indicate when metrics are "not_found"
- Provide context and interpretation, not just numbers
- Be objective and balanced in assessment
- Format as clean Markdown with proper headers and sections

Generate the report now:"""),
                ("human", "KPI Data:\n{kpi_data}")
            ])
            
            # Generate report
            formatted_prompt = prompt.format_messages(kpi_data=kpi_summary)
            response = self.llm.invoke(formatted_prompt)
            
            if hasattr(response, 'content'):
                report = response.content
            else:
                report = str(response)
            
            # Ensure proper Markdown formatting
            report = self._ensure_markdown_format(report)
            
            logger.info("Generated KPI report")
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            # Return a basic report structure
            return self._generate_fallback_report(kpi_data)
    
    def _format_kpi_data(self, kpi_data: Dict[str, Any]) -> str:
        """Format KPI data for prompt."""
        lines = []
        lines.append("## Extracted KPI Data\n")
        
        # Financial Metrics
        lines.append("### Financial Metrics")
        lines.append(f"- Revenue: {kpi_data.get('revenue', 'not_found')}")
        lines.append(f"- Net Profit: {kpi_data.get('net_profit', 'not_found')}")
        lines.append(f"- ROE: {kpi_data.get('roe', 'not_found')}%")
        lines.append(f"- ROA: {kpi_data.get('roa', 'not_found')}%")
        lines.append("")
        
        # Asset Quality
        lines.append("### Asset Quality")
        lines.append(f"- GNPA: {kpi_data.get('gnpa', 'not_found')}%")
        lines.append(f"- NNPA: {kpi_data.get('nnpa', 'not_found')}%")
        lines.append(f"- PCR: {kpi_data.get('pcr', 'not_found')}%")
        lines.append("")
        
        # Capital Adequacy
        lines.append("### Capital Adequacy")
        lines.append(f"- CRAR: {kpi_data.get('crar', 'not_found')}%")
        lines.append(f"- CAR: {kpi_data.get('car', 'not_found')}%")
        lines.append("")
        
        # Growth Metrics
        lines.append("### Growth Metrics")
        lines.append(f"- Revenue Growth QoQ: {kpi_data.get('revenue_growth_qoq', 'not_found')}%")
        lines.append(f"- Revenue Growth YoY: {kpi_data.get('revenue_growth_yoy', 'not_found')}%")
        lines.append(f"- Profit Growth QoQ: {kpi_data.get('profit_growth_qoq', 'not_found')}%")
        lines.append(f"- Profit Growth YoY: {kpi_data.get('profit_growth_yoy', 'not_found')}%")
        lines.append("")
        
        # Metadata
        if kpi_data.get('currency'):
            lines.append(f"**Currency:** {kpi_data['currency']}")
        if kpi_data.get('period'):
            lines.append(f"**Period:** {kpi_data['period']}")
        
        return "\n".join(lines)
    
    def _ensure_markdown_format(self, report: str) -> str:
        """Ensure report has proper Markdown formatting."""
        # Add title if missing
        if not report.startswith("#"):
            report = "# BFSI Financial Report\n\n" + report
        
        return report
    
    def _generate_fallback_report(self, kpi_data: Dict[str, Any]) -> str:
        """Generate a basic fallback report if LLM fails."""
        report = """# BFSI Financial Report

## Executive Summary

This report contains extracted financial metrics from the document. Some metrics may not be available.

## Key Financial Highlights

- Revenue: {revenue}
- Net Profit: {net_profit}
- ROE: {roe}%
- ROA: {roa}%

## Risk & Asset Quality

- GNPA: {gnpa}%
- NNPA: {nnpa}%
- PCR: {pcr}%

## Capital Adequacy

- CRAR: {crar}%
- CAR: {car}%

## Trends & Red Flags

Analysis based on available metrics. Please review the extracted data for detailed insights.
""".format(**kpi_data)
        
        return report
