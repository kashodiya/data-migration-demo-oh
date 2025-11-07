"""
HTML Report Generator
Generates comprehensive HTML reports for migration operations
"""

import json
import os
from datetime import datetime
from pathlib import Path


class HTMLReportGenerator:
    """Generates static HTML reports for migration operations"""
    
    def __init__(self, output_dir="reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_migration_report(self, migration_data, report_name=None):
        """Generate a comprehensive migration report"""
        if not report_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"migration_report_{timestamp}.html"
        
        report_path = self.output_dir / report_name
        
        html_content = self._build_html_report(migration_data)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_path)
    
    def _build_html_report(self, data):
        """Build the complete HTML report"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Migration Report - {data.get('migration_id', 'Unknown')}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        {self._build_header(data)}
        {self._build_summary_section(data)}
        {self._build_tables_section(data)}
        {self._build_timeline_section(data)}
        {self._build_errors_section(data)}
        {self._build_validation_section(data)}
        {self._build_footer()}
    </div>
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>
"""
    
    def _get_css_styles(self):
        """Return CSS styles for the report"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .section {
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .section-header {
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .section-header h2 {
            color: #495057;
            font-size: 1.5em;
        }
        
        .section-content {
            padding: 20px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        
        .summary-card h3 {
            color: #495057;
            margin-bottom: 10px;
        }
        
        .summary-card .value {
            font-size: 1.8em;
            font-weight: bold;
            color: #007bff;
        }
        
        .table-card {
            border: 1px solid #e9ecef;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }
        
        .table-header {
            background: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .table-header h3 {
            color: #495057;
            margin-bottom: 5px;
        }
        
        .table-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            padding: 15px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #28a745;
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #6c757d;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .status-completed {
            background: #d4edda;
            color: #155724;
        }
        
        .status-in-progress {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-failed {
            background: #f8d7da;
            color: #721c24;
        }
        
        .timeline {
            position: relative;
            padding-left: 30px;
        }
        
        .timeline::before {
            content: '';
            position: absolute;
            left: 15px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #e9ecef;
        }
        
        .timeline-item {
            position: relative;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -22px;
            top: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #007bff;
        }
        
        .error-item {
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        
        .error-title {
            font-weight: bold;
            color: #721c24;
            margin-bottom: 5px;
        }
        
        .error-message {
            color: #721c24;
            font-family: monospace;
        }
        
        .validation-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .validation-card {
            border: 1px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .validation-header {
            background: #f8f9fa;
            padding: 15px;
            font-weight: bold;
        }
        
        .validation-content {
            padding: 15px;
        }
        
        .validation-check {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .check-passed {
            color: #28a745;
            font-weight: bold;
        }
        
        .check-failed {
            color: #dc3545;
            font-weight: bold;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #6c757d;
            border-top: 1px solid #e9ecef;
            margin-top: 30px;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .table-stats {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        """
    
    def _build_header(self, data):
        """Build the report header"""
        migration_id = data.get('migration_id', 'Unknown')
        start_time = data.get('start_time', 'Unknown')
        
        return f"""
        <div class="header">
            <h1>Migration Report</h1>
            <div class="subtitle">Migration ID: {migration_id}</div>
            <div class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        """
    
    def _build_summary_section(self, data):
        """Build the summary section"""
        summary = data.get('summary', {})
        
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>Migration Summary</h2>
            </div>
            <div class="section-content">
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>Status</h3>
                        <div class="value">{summary.get('status', 'Unknown')}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Total Tables</h3>
                        <div class="value">{summary.get('total_tables', 0)}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Records Migrated</h3>
                        <div class="value">{summary.get('total_records', 0):,}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Duration</h3>
                        <div class="value">{summary.get('duration', 'Unknown')}</div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _build_tables_section(self, data):
        """Build the tables section"""
        tables = data.get('tables', {})
        
        tables_html = ""
        for table_name, table_data in tables.items():
            status = table_data.get('status', 'unknown')
            records_migrated = table_data.get('records_migrated', 0)
            total_records = table_data.get('total_records', 0)
            
            progress_percentage = 0
            if total_records > 0:
                progress_percentage = (records_migrated / total_records) * 100
            
            status_class = f"status-{status.replace('_', '-')}"
            
            tables_html += f"""
            <div class="table-card">
                <div class="table-header">
                    <h3>{table_name}</h3>
                    <span class="status-badge {status_class}">{status}</span>
                </div>
                <div class="table-stats">
                    <div class="stat-item">
                        <div class="stat-value">{records_migrated:,}</div>
                        <div class="stat-label">Records Migrated</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{total_records:,}</div>
                        <div class="stat-label">Total Records</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{progress_percentage:.1f}%</div>
                        <div class="stat-label">Progress</div>
                    </div>
                </div>
                <div style="padding: 0 15px 15px;">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress_percentage}%"></div>
                    </div>
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>Table Migration Details</h2>
            </div>
            <div class="section-content">
                {tables_html}
            </div>
        </div>
        """
    
    def _build_timeline_section(self, data):
        """Build the timeline section"""
        timeline = data.get('timeline', [])
        
        timeline_html = ""
        for event in timeline:
            timestamp = event.get('timestamp', 'Unknown')
            message = event.get('message', 'No message')
            
            timeline_html += f"""
            <div class="timeline-item">
                <strong>{timestamp}</strong><br>
                {message}
            </div>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>Migration Timeline</h2>
            </div>
            <div class="section-content">
                <div class="timeline">
                    {timeline_html}
                </div>
            </div>
        </div>
        """
    
    def _build_errors_section(self, data):
        """Build the errors section"""
        errors = data.get('errors', [])
        
        if not errors:
            return f"""
            <div class="section">
                <div class="section-header">
                    <h2>Errors and Issues</h2>
                </div>
                <div class="section-content">
                    <p style="color: #28a745; font-weight: bold;">✓ No errors encountered during migration</p>
                </div>
            </div>
            """
        
        errors_html = ""
        for error in errors:
            table = error.get('table', 'General')
            message = error.get('message', 'Unknown error')
            timestamp = error.get('timestamp', 'Unknown')
            
            errors_html += f"""
            <div class="error-item">
                <div class="error-title">{table} - {timestamp}</div>
                <div class="error-message">{message}</div>
            </div>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>Errors and Issues</h2>
            </div>
            <div class="section-content">
                {errors_html}
            </div>
        </div>
        """
    
    def _build_validation_section(self, data):
        """Build the validation section"""
        validation = data.get('validation', {})
        
        if not validation:
            return ""
        
        validation_html = ""
        for table_name, results in validation.items():
            count_match = results.get('count_match', False)
            source_count = results.get('source_count', 0)
            target_count = results.get('target_count', 0)
            
            count_status = "✓ Passed" if count_match else "✗ Failed"
            count_class = "check-passed" if count_match else "check-failed"
            
            validation_html += f"""
            <div class="validation-card">
                <div class="validation-header">{table_name}</div>
                <div class="validation-content">
                    <div class="validation-check">
                        <span>Record Count Match</span>
                        <span class="{count_class}">{count_status}</span>
                    </div>
                    <div class="validation-check">
                        <span>Source Records</span>
                        <span>{source_count:,}</span>
                    </div>
                    <div class="validation-check">
                        <span>Target Records</span>
                        <span>{target_count:,}</span>
                    </div>
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <div class="section-header">
                <h2>Data Validation Results</h2>
            </div>
            <div class="section-content">
                <div class="validation-grid">
                    {validation_html}
                </div>
            </div>
        </div>
        """
    
    def _build_footer(self):
        """Build the report footer"""
        return f"""
        <div class="footer">
            <p>Report generated by Chinook Migration Tool on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """
    
    def _get_javascript(self):
        """Return JavaScript for interactive features"""
        return """
        // Add any interactive features here
        document.addEventListener('DOMContentLoaded', function() {
            // Animate progress bars
            const progressBars = document.querySelectorAll('.progress-fill');
            progressBars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            });
        });
        """
