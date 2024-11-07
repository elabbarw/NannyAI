import os
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import io
from utils.logger import get_logger

class ReportGenerator:
    def __init__(self, screenshot_history, device_manager):
        self.logger = get_logger(__name__)
        self.screenshot_history = screenshot_history
        self.device_manager = device_manager
        self.reports_dir = "data/reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_report(self, start_date=None, end_date=None, device_id=None):
        """Generate a comprehensive activity report"""
        try:
            # Default to last 7 days if no dates specified
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            # Get relevant screenshots
            entries = self._get_filtered_entries(start_date, end_date, device_id)
            if not entries:
                self.logger.warning("No data available for the specified period")
                return None

            # Create report filename
            device_info = f"_{self.device_manager.get_device(device_id).name}" if device_id else ""
            filename = f"activity_report{device_info}_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.pdf"
            filepath = os.path.join(self.reports_dir, filename)

            # Generate PDF
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Add title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            story.append(Paragraph("Screen Content Monitor Report", title_style))
            story.append(Spacer(1, 12))

            # Add report period
            period_text = f"Report Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            story.append(Paragraph(period_text, styles['Heading2']))
            story.append(Spacer(1, 12))

            # Add summary statistics
            story.extend(self._create_summary_section(entries))
            story.append(Spacer(1, 20))

            # Add alert trends graph
            story.extend(self._create_trends_section(entries))
            story.append(Spacer(1, 20))

            # Add device activity summary
            if not device_id:
                story.extend(self._create_device_summary_section(entries))
                story.append(Spacer(1, 20))

            # Add detailed alerts table
            story.extend(self._create_alerts_section(entries))

            # Build PDF
            doc.build(story)
            self.logger.info(f"Report generated successfully: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"Failed to generate report: {str(e)}")
            return None

    def _get_filtered_entries(self, start_date, end_date, device_id=None):
        """Get filtered screenshot entries"""
        entries = self.screenshot_history.get_history()
        filtered_entries = []
        
        for entry in entries:
            timestamp = datetime.fromisoformat(entry['timestamp'])
            if start_date <= timestamp <= end_date:
                if device_id is None or entry.get('device_id') == device_id:
                    filtered_entries.append(entry)
        
        return filtered_entries

    def _create_summary_section(self, entries):
        """Create summary statistics section"""
        styles = getSampleStyleSheet()
        elements = []
        
        # Calculate statistics
        total_screenshots = len(entries)
        alerts_by_category = {
            'violence': 0,
            'adult': 0,
            'hate': 0,
            'drugs': 0,
            'gambling': 0
        }
        
        for entry in entries:
            analysis = entry.get('analysis', {})
            for category, score in analysis.items():
                if category in alerts_by_category and score >= 0.7:
                    alerts_by_category[category] += 1

        # Create summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Screenshots', str(total_screenshots)],
            ['Violence Alerts', str(alerts_by_category['violence'])],
            ['Adult Content Alerts', str(alerts_by_category['adult'])],
            ['Hate Content Alerts', str(alerts_by_category['hate'])],
            ['Drug-related Alerts', str(alerts_by_category['drugs'])],
            ['Gambling-related Alerts', str(alerts_by_category['gambling'])]
        ]

        table = Table(summary_data, colWidths=[3*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(Paragraph("Summary Statistics", styles['Heading2']))
        elements.append(Spacer(1, 12))
        elements.append(table)
        
        return elements

    def _create_trends_section(self, entries):
        """Create trends visualization section"""
        styles = getSampleStyleSheet()
        elements = []

        # Create trends graph
        plt.figure(figsize=(8, 4))
        dates = sorted(list({datetime.fromisoformat(e['timestamp']).date() for e in entries}))
        
        alerts_by_date = {
            'violence': [0] * len(dates),
            'adult': [0] * len(dates),
            'hate': [0] * len(dates),
            'drugs': [0] * len(dates),
            'gambling': [0] * len(dates)
        }

        for entry in entries:
            date = datetime.fromisoformat(entry['timestamp']).date()
            date_index = dates.index(date)
            analysis = entry.get('analysis', {})
            
            for category in alerts_by_date.keys():
                if analysis.get(category, 0) >= 0.7:
                    alerts_by_date[category][date_index] += 1

        # Plot trends
        plt.clf()
        for category, values in alerts_by_date.items():
            plt.plot(dates, values, marker='o', label=category.capitalize())

        plt.title('Alert Trends Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Alerts')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()

        # Save plot to bytes buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)

        # Add to PDF
        elements.append(Paragraph("Alert Trends", styles['Heading2']))
        elements.append(Spacer(1, 12))
        elements.append(Image(img_buffer, width=6*inch, height=3*inch))
        
        return elements

    def _create_device_summary_section(self, entries):
        """Create device activity summary section"""
        styles = getSampleStyleSheet()
        elements = []

        # Group entries by device
        device_stats = {}
        for entry in entries:
            device_id = entry.get('device_id')
            if device_id:
                if device_id not in device_stats:
                    device = self.device_manager.get_device(device_id)
                    device_stats[device_id] = {
                        'name': device.name if device else 'Unknown Device',
                        'screenshots': 0,
                        'alerts': 0
                    }
                
                device_stats[device_id]['screenshots'] += 1
                analysis = entry.get('analysis', {})
                if any(score >= 0.7 for score in analysis.values()):
                    device_stats[device_id]['alerts'] += 1

        # Create device summary table
        if device_stats:
            table_data = [['Device', 'Screenshots', 'Alerts']]
            for stats in device_stats.values():
                table_data.append([
                    stats['name'],
                    str(stats['screenshots']),
                    str(stats['alerts'])
                ])

            table = Table(table_data, colWidths=[2.5*inch, 2*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(Paragraph("Device Activity Summary", styles['Heading2']))
            elements.append(Spacer(1, 12))
            elements.append(table)

        return elements

    def _create_alerts_section(self, entries):
        """Create detailed alerts section"""
        styles = getSampleStyleSheet()
        elements = []

        # Filter entries with alerts
        alert_entries = [
            entry for entry in entries
            if any(float(score) >= 0.7 for score in entry.get('analysis', {}).values())
        ]

        if alert_entries:
            table_data = [['Date/Time', 'Device', 'Categories', 'Scores']]
            
            for entry in alert_entries:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                device = self.device_manager.get_device(entry.get('device_id'))
                device_name = device.name if device else 'Unknown Device'
                
                # Format alert categories and scores
                analysis = entry.get('analysis', {})
                alert_cats = []
                alert_scores = []
                
                for category, score in analysis.items():
                    if score >= 0.7:
                        alert_cats.append(category.capitalize())
                        alert_scores.append(f"{score:.2f}")

                table_data.append([
                    timestamp.strftime('%Y-%m-%d %H:%M'),
                    device_name,
                    '\n'.join(alert_cats),
                    '\n'.join(alert_scores)
                ])

            table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 2*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(Paragraph("Detailed Alerts", styles['Heading2']))
            elements.append(Spacer(1, 12))
            elements.append(table)

        return elements
