"""
Compliance Report Export Handler
===============================
Handles export of compliance reports to various formats (PDF, Excel, CSV, JSON, XML)
with customizable templates and formatting options.
"""
import logging
import json
import csv
import io
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
import base64

from .models import (
    ReportFormat, ComplianceReport, AuditTrail, 
    ComplianceMetrics, DashboardConfiguration
)

logger = logging.getLogger(__name__)


class ExportTemplate:
    """Export template configuration."""
    
    def __init__(
        self,
        template_id: str,
        name: str,
        format_type: ReportFormat,
        template_config: Dict[str, Any]
    ):
        self.template_id = template_id
        self.name = name
        self.format_type = format_type
        self.template_config = template_config


class ComplianceReportExporter:
    """
    Handles export of compliance reports to multiple formats with
    customizable templates and professional formatting.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.export_templates = self._initialize_export_templates()
        self.format_handlers = {
            ReportFormat.PDF: self._export_to_pdf,
            ReportFormat.EXCEL: self._export_to_excel,
            ReportFormat.CSV: self._export_to_csv,
            ReportFormat.JSON: self._export_to_json,
            ReportFormat.XML: self._export_to_xml
        }

    def _initialize_export_templates(self) -> Dict[str, ExportTemplate]:
        """Initialize predefined export templates."""
        templates = {}
        
        # Executive Summary PDF Template
        templates["executive_pdf"] = ExportTemplate(
            template_id="executive_pdf",
            name="Executive Summary PDF",
            format_type=ReportFormat.PDF,
            template_config={
                "page_size": "A4",
                "orientation": "portrait",
                "margins": {"top": 1, "bottom": 1, "left": 1, "right": 1},
                "header": {
                    "include": True,
                    "logo": True,
                    "title": True,
                    "date": True
                },
                "footer": {
                    "include": True,
                    "page_numbers": True,
                    "organization": True
                },
                "sections": [
                    "executive_summary",
                    "compliance_overview", 
                    "risk_analysis",
                    "recommendations"
                ],
                "charts": True,
                "detailed_data": False
            }
        )
        
        # Detailed Audit Excel Template
        templates["audit_excel"] = ExportTemplate(
            template_id="audit_excel",
            name="Detailed Audit Excel",
            format_type=ReportFormat.EXCEL,
            template_config={
                "worksheets": [
                    {"name": "Summary", "type": "summary"},
                    {"name": "Audit Trail", "type": "audit_data"},
                    {"name": "Metrics", "type": "metrics"},
                    {"name": "Charts", "type": "charts"}
                ],
                "formatting": {
                    "header_style": "bold",
                    "freeze_panes": True,
                    "auto_filter": True,
                    "conditional_formatting": True
                },
                "charts": True,
                "pivot_tables": True
            }
        )
        
        # Regulatory Submission XML Template
        templates["regulatory_xml"] = ExportTemplate(
            template_id="regulatory_xml",
            name="Regulatory Submission XML",
            format_type=ReportFormat.XML,
            template_config={
                "schema_version": "1.0",
                "namespace": "urn:taxpoynt:compliance:reporting",
                "include_metadata": True,
                "validation": True,
                "encoding": "UTF-8"
            }
        )
        
        return templates

    async def export_compliance_report(
        self,
        report_data: Dict[str, Any],
        export_format: ReportFormat,
        template_id: Optional[str] = None,
        custom_config: Optional[Dict[str, Any]] = None,
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export compliance report to specified format.
        
        Args:
            report_data: Report data to export
            export_format: Target export format
            template_id: Template to use for export
            custom_config: Custom configuration options
            output_filename: Custom output filename
            
        Returns:
            Export result with file info and metadata
        """
        try:
            self.logger.info(f"Exporting compliance report to {export_format.value}")
            
            # Get export handler
            if export_format not in self.format_handlers:
                raise ValueError(f"Unsupported export format: {export_format.value}")
            
            handler = self.format_handlers[export_format]
            
            # Get template configuration
            template_config = {}
            if template_id and template_id in self.export_templates:
                template_config = self.export_templates[template_id].template_config
            
            # Merge with custom configuration
            if custom_config:
                template_config.update(custom_config)
            
            # Generate filename if not provided
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                org_id = report_data.get("organization_id", "unknown")
                output_filename = f"compliance_report_{org_id}_{timestamp}.{export_format.value.lower()}"
            
            # Execute export
            export_result = await handler(report_data, template_config, output_filename)
            
            # Add export metadata
            export_result.update({
                "export_id": str(uuid.uuid4()),
                "exported_at": datetime.now().isoformat(),
                "format": export_format.value,
                "template_id": template_id,
                "filename": output_filename
            })
            
            self.logger.info(f"Report exported successfully: {output_filename}")
            return export_result
            
        except Exception as e:
            self.logger.error(f"Error exporting compliance report: {str(e)}")
            raise

    async def _export_to_pdf(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """Export report to PDF format."""
        try:
            # Note: In production, would use libraries like reportlab, weasyprint, or pdfkit
            # This is a simplified implementation for demonstration
            
            pdf_content = self._generate_pdf_content(report_data, template_config)
            
            return {
                "content": pdf_content,
                "content_type": "application/pdf",
                "size_bytes": len(pdf_content),
                "pages": self._calculate_pdf_pages(report_data, template_config)
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting to PDF: {str(e)}")
            raise

    async def _export_to_excel(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """Export report to Excel format."""
        try:
            # Note: In production, would use libraries like openpyxl or xlsxwriter
            # This is a simplified implementation for demonstration
            
            excel_content = self._generate_excel_content(report_data, template_config)
            
            return {
                "content": excel_content,
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "size_bytes": len(excel_content),
                "worksheets": len(template_config.get("worksheets", []))
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {str(e)}")
            raise

    async def _export_to_csv(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """Export report to CSV format."""
        try:
            csv_content = self._generate_csv_content(report_data, template_config)
            
            return {
                "content": csv_content.encode('utf-8'),
                "content_type": "text/csv",
                "size_bytes": len(csv_content.encode('utf-8')),
                "encoding": "utf-8"
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {str(e)}")
            raise

    async def _export_to_json(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """Export report to JSON format."""
        try:
            json_content = self._generate_json_content(report_data, template_config)
            
            return {
                "content": json_content.encode('utf-8'),
                "content_type": "application/json",
                "size_bytes": len(json_content.encode('utf-8')),
                "encoding": "utf-8"
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {str(e)}")
            raise

    async def _export_to_xml(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any],
        filename: str
    ) -> Dict[str, Any]:
        """Export report to XML format."""
        try:
            xml_content = self._generate_xml_content(report_data, template_config)
            
            return {
                "content": xml_content.encode('utf-8'),
                "content_type": "application/xml",
                "size_bytes": len(xml_content.encode('utf-8')),
                "encoding": "utf-8"
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting to XML: {str(e)}")
            raise

    def _generate_pdf_content(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any]
    ) -> bytes:
        """Generate PDF content (simplified implementation)."""
        # This would integrate with a proper PDF library in production
        html_content = self._generate_html_for_pdf(report_data, template_config)
        
        # Placeholder: Convert HTML to PDF bytes
        # In production: use weasyprint.HTML(string=html_content).write_pdf()
        pdf_placeholder = f"PDF Report Content\n{html_content}"
        return pdf_placeholder.encode('utf-8')

    def _generate_excel_content(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any]
    ) -> bytes:
        """Generate Excel content (simplified implementation)."""
        # This would integrate with openpyxl or xlsxwriter in production
        excel_data = {
            "summary": self._extract_summary_data(report_data),
            "metrics": self._extract_metrics_data(report_data),
            "audit_trail": self._extract_audit_data(report_data)
        }
        
        # Placeholder: Create Excel file bytes
        excel_placeholder = json.dumps(excel_data, indent=2, default=str)
        return excel_placeholder.encode('utf-8')

    def _generate_csv_content(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any]
    ) -> str:
        """Generate CSV content."""
        output = io.StringIO()
        
        # Extract tabular data for CSV
        if "audit_records" in report_data:
            audit_records = report_data["audit_records"]
            if audit_records:
                # Get field names from first record
                fieldnames = list(audit_records[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in audit_records:
                    # Flatten nested objects for CSV
                    flattened_record = self._flatten_dict(record)
                    writer.writerow(flattened_record)
        
        elif "metrics" in report_data:
            metrics = report_data["metrics"]
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value", "Description"])
            
            for key, value in metrics.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        writer.writerow([f"{key}.{sub_key}", sub_value, ""])
                else:
                    writer.writerow([key, value, ""])
        
        return output.getvalue()

    def _generate_json_content(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any]
    ) -> str:
        """Generate JSON content."""
        # Apply template configuration filtering
        filtered_data = self._apply_json_template(report_data, template_config)
        
        return json.dumps(filtered_data, indent=2, default=str, ensure_ascii=False)

    def _generate_xml_content(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any]
    ) -> str:
        """Generate XML content."""
        namespace = template_config.get("namespace", "urn:taxpoynt:compliance")
        schema_version = template_config.get("schema_version", "1.0")
        
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<ComplianceReport xmlns="{namespace}" version="{schema_version}">'
        ]
        
        # Add metadata
        if template_config.get("include_metadata", True):
            xml_lines.extend([
                '  <Metadata>',
                f'    <ReportId>{report_data.get("report_id", "")}</ReportId>',
                f'    <OrganizationId>{report_data.get("organization_id", "")}</OrganizationId>',
                f'    <GeneratedAt>{report_data.get("generated_at", "")}</GeneratedAt>',
                f'    <ReportType>{report_data.get("report_type", "")}</ReportType>',
                '  </Metadata>'
            ])
        
        # Add summary
        if "summary" in report_data:
            xml_lines.append('  <Summary>')
            xml_lines.extend(self._dict_to_xml(report_data["summary"], indent=4))
            xml_lines.append('  </Summary>')
        
        # Add metrics
        if "metrics" in report_data:
            xml_lines.append('  <Metrics>')
            xml_lines.extend(self._dict_to_xml(report_data["metrics"], indent=4))
            xml_lines.append('  </Metrics>')
        
        xml_lines.append('</ComplianceReport>')
        
        return '\n'.join(xml_lines)

    def _generate_html_for_pdf(
        self,
        report_data: Dict[str, Any],
        template_config: Dict[str, Any]
    ) -> str:
        """Generate HTML content for PDF conversion."""
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '  <meta charset="UTF-8">',
            f'  <title>Compliance Report - {report_data.get("organization_id", "")}</title>',
            '  <style>',
            '    body { font-family: Arial, sans-serif; margin: 40px; }',
            '    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }',
            '    h2 { color: #34495e; margin-top: 30px; }',
            '    table { width: 100%; border-collapse: collapse; margin: 20px 0; }',
            '    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }',
            '    th { background-color: #f2f2f2; font-weight: bold; }',
            '    .metric { background-color: #f8f9fa; padding: 10px; margin: 10px 0; }',
            '  </style>',
            '</head>',
            '<body>'
        ]
        
        # Add header
        if template_config.get("header", {}).get("include", True):
            html_parts.extend([
                f'<h1>Compliance Report</h1>',
                f'<p><strong>Organization:</strong> {report_data.get("organization_id", "")}</p>',
                f'<p><strong>Generated:</strong> {report_data.get("generated_at", "")}</p>',
                f'<p><strong>Report Type:</strong> {report_data.get("report_type", "")}</p>'
            ])
        
        # Add sections based on template configuration
        sections = template_config.get("sections", ["summary", "metrics"])
        
        if "summary" in sections and "summary" in report_data:
            html_parts.append('<h2>Executive Summary</h2>')
            html_parts.extend(self._dict_to_html_table(report_data["summary"]))
        
        if "metrics" in sections and "metrics" in report_data:
            html_parts.append('<h2>Compliance Metrics</h2>')
            html_parts.extend(self._dict_to_html_table(report_data["metrics"]))
        
        html_parts.extend(['</body>', '</html>'])
        
        return '\n'.join(html_parts)

    def _extract_summary_data(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract summary data for Excel export."""
        return report_data.get("summary", {})

    def _extract_metrics_data(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics data for Excel export."""
        return report_data.get("metrics", {})

    def _extract_audit_data(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract audit data for Excel export."""
        return report_data.get("audit_records", [])

    def _flatten_dict(self, obj: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export."""
        items = []
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to string representation
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    def _apply_json_template(self, data: Dict[str, Any], template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply JSON template configuration to filter data."""
        if not template_config:
            return data
        
        # Include only specified fields if configured
        include_fields = template_config.get("include_fields")
        if include_fields:
            filtered_data = {k: v for k, v in data.items() if k in include_fields}
        else:
            filtered_data = data.copy()
        
        # Exclude specified fields if configured
        exclude_fields = template_config.get("exclude_fields", [])
        for field in exclude_fields:
            filtered_data.pop(field, None)
        
        return filtered_data

    def _dict_to_xml(self, obj: Dict[str, Any], indent: int = 0) -> List[str]:
        """Convert dictionary to XML lines."""
        lines = []
        spaces = ' ' * indent
        
        for key, value in obj.items():
            # Sanitize key for XML
            xml_key = key.replace(' ', '_').replace('-', '_')
            
            if isinstance(value, dict):
                lines.append(f'{spaces}<{xml_key}>')
                lines.extend(self._dict_to_xml(value, indent + 2))
                lines.append(f'{spaces}</{xml_key}>')
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f'{spaces}<{xml_key}>')
                        lines.extend(self._dict_to_xml(item, indent + 2))
                        lines.append(f'{spaces}</{xml_key}>')
                    else:
                        lines.append(f'{spaces}<{xml_key}>{self._escape_xml(str(item))}</{xml_key}>')
            else:
                lines.append(f'{spaces}<{xml_key}>{self._escape_xml(str(value))}</{xml_key}>')
        
        return lines

    def _dict_to_html_table(self, obj: Dict[str, Any]) -> List[str]:
        """Convert dictionary to HTML table."""
        lines = ['<table>']
        
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            
            lines.extend([
                '<tr>',
                f'  <th>{key}</th>',
                f'  <td>{value_str}</td>',
                '</tr>'
            ])
        
        lines.append('</table>')
        return lines

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))

    def _calculate_pdf_pages(self, report_data: Dict[str, Any], template_config: Dict[str, Any]) -> int:
        """Estimate number of PDF pages."""
        # Simplified page estimation
        content_sections = len(template_config.get("sections", []))
        audit_records = len(report_data.get("audit_records", []))
        
        # Rough estimation: 1 page per section + 1 page per 20 audit records
        estimated_pages = content_sections + (audit_records // 20) + 1
        return max(1, estimated_pages)