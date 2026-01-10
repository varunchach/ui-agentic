"""KPI Report view component."""

import streamlit as st
from app.utils.export import ReportExporter


def render_kpi_report(report: str, kpi_data: dict, execution_time: float = None):
    """Render KPI report view.
    
    Args:
        report: Markdown report content
        kpi_data: Extracted KPI data dictionary
        execution_time: Optional execution time in seconds
    """
    st.header("📊 KPI Report")
    
    # Display execution time if available
    if execution_time is not None:
        time_str = f"{execution_time:.2f}s" if execution_time < 60 else f"{execution_time/60:.1f}m"
        st.caption(f"⏱️ Generated in {time_str}")
    
    # Display report
    st.markdown("---")
    st.markdown(report)
    
    # Export options
    st.markdown("---")
    st.subheader("📥 Export Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download as Markdown", use_container_width=True):
            exporter = ReportExporter()
            file_bytes, filename = exporter.export_markdown(report)
            st.download_button(
                label="⬇️ Download Markdown",
                data=file_bytes,
                file_name=filename,
                mime="text/markdown",
                use_container_width=True
            )
    
    with col2:
        if st.button("Download as PDF", use_container_width=True):
            try:
                exporter = ReportExporter()
                file_bytes, filename = exporter.export_pdf(report)
                st.download_button(
                    label="⬇️ Download PDF",
                    data=file_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
    
    # KPI Data Summary (collapsible)
    with st.expander("📈 View Raw KPI Data"):
        st.json(kpi_data)
