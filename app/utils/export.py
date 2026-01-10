"""Report export functionality (Markdown and PDF)."""

import logging
from pathlib import Path
from typing import Optional
from io import BytesIO

logger = logging.getLogger(__name__)


class ReportExporter:
    """Export reports in various formats."""
    
    @staticmethod
    def export_markdown(report: str, filename: Optional[str] = None) -> tuple[bytes, str]:
        """Export report as Markdown file.
        
        Args:
            report: Markdown report content
            filename: Optional filename (defaults to 'bfsi_report.md')
            
        Returns:
            Tuple of (file_bytes, filename)
        """
        filename = filename or "bfsi_report.md"
        
        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'
        
        file_bytes = report.encode('utf-8')
        
        logger.info(f"Exported Markdown report: {filename}")
        return file_bytes, filename
    
    @staticmethod
    def export_pdf(report: str, filename: Optional[str] = None) -> tuple[bytes, str]:
        """Export report as PDF file.
        
        Args:
            report: Markdown report content
            filename: Optional filename (defaults to 'bfsi_report.pdf')
            
        Returns:
            Tuple of (file_bytes, filename)
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
            import markdown2
            
            filename = filename or "bfsi_report.pdf"
            
            # Ensure .pdf extension
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            # Convert Markdown to HTML
            html = markdown2.markdown(report)
            
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor='#1a1a1a',
                spaceAfter=12,
                alignment=TA_CENTER
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor='#2c3e50',
                spaceAfter=10,
                spaceBefore=12
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                textColor='#333333',
                spaceAfter=6,
                alignment=TA_LEFT
            )
            
            # Build PDF content
            story = []
            
            # Parse HTML and create paragraphs
            # Simple HTML to PDF conversion (basic implementation)
            lines = report.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 6))
                    continue
                
                # Handle headers
                if line.startswith('# '):
                    story.append(Paragraph(line[2:], title_style))
                    story.append(Spacer(1, 12))
                elif line.startswith('## '):
                    story.append(Paragraph(line[3:], heading_style))
                    story.append(Spacer(1, 10))
                elif line.startswith('### '):
                    story.append(Paragraph(line[4:], heading_style))
                    story.append(Spacer(1, 8))
                else:
                    # Clean up markdown formatting
                    clean_line = line
                    # Remove markdown bold/italic
                    clean_line = clean_line.replace('**', '').replace('*', '')
                    # Remove markdown links
                    import re
                    clean_line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_line)
                    
                    if clean_line:
                        story.append(Paragraph(clean_line, normal_style))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Exported PDF report: {filename}")
            return pdf_bytes, filename
            
        except ImportError:
            logger.error("reportlab or markdown2 not installed. Cannot export PDF.")
            raise ImportError(
                "PDF export requires reportlab and markdown2. "
                "Install with: pip install reportlab markdown2"
            )
        except Exception as e:
            logger.error(f"Error exporting PDF: {str(e)}")
            raise
