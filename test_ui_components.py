"""UI components for dashboard and data visualization."""

from typing import List, Dict, Any, Optional
from datetime import datetime

class DashboardWidget:
    """Base class for dashboard widgets."""
    
    def __init__(self, title: str, width: int = 12, height: int = 4):
        self.title = title
        self.width = width  # Grid width (1-12)
        self.height = height  # Grid height units
        self.created_at = datetime.now()
    
    def render(self) -> Dict[str, Any]:
        """Render widget to JSON representation."""
        return {
            'type': self.__class__.__name__,
            'title': self.title,
            'width': self.width,
            'height': self.height,
            'content': self.get_content()
        }
    
    def get_content(self) -> Dict[str, Any]:
        """Override in subclasses to provide specific content."""
        return {}

class ChartWidget(DashboardWidget):
    """Widget for displaying charts and graphs."""
    
    def __init__(self, title: str, chart_type: str = "line", data: List[Dict] = None):
        super().__init__(title)
        self.chart_type = chart_type  # line, bar, pie, scatter
        self.data = data or []
        self.chart_config = {
            'responsive': True,
            'animate': True,
            'theme': 'light'
        }
    
    def add_data_point(self, label: str, value: float, color: Optional[str] = None):
        """Add a data point to the chart."""
        data_point = {'label': label, 'value': value}
        if color:
            data_point['color'] = color
        self.data.append(data_point)
    
    def set_chart_config(self, config: Dict[str, Any]):
        """Update chart configuration."""
        self.chart_config.update(config)
    
    def get_content(self) -> Dict[str, Any]:
        """Get chart content for rendering."""
        return {
            'chart_type': self.chart_type,
            'data': self.data,
            'config': self.chart_config
        }

class MetricWidget(DashboardWidget):
    """Widget for displaying key metrics and KPIs."""
    
    def __init__(self, title: str, metric_value: float, unit: str = "", 
                 trend: Optional[str] = None, target: Optional[float] = None):
        super().__init__(title, width=3, height=2)
        self.metric_value = metric_value
        self.unit = unit
        self.trend = trend  # "up", "down", "stable"
        self.target = target
        self.format_type = "number"  # number, percentage, currency
    
    def set_format(self, format_type: str):
        """Set the display format for the metric."""
        valid_formats = ["number", "percentage", "currency"]
        if format_type in valid_formats:
            self.format_type = format_type
    
    def update_value(self, new_value: float, new_trend: Optional[str] = None):
        """Update the metric value and trend."""
        self.metric_value = new_value
        if new_trend:
            self.trend = new_trend
    
    def get_content(self) -> Dict[str, Any]:
        """Get metric content for rendering."""
        content = {
            'value': self.metric_value,
            'unit': self.unit,
            'format': self.format_type
        }
        
        if self.trend:
            content['trend'] = self.trend
        
        if self.target:
            content['target'] = self.target
            content['progress'] = (self.metric_value / self.target) * 100
        
        return content

class DataTableWidget(DashboardWidget):
    """Widget for displaying tabular data."""
    
    def __init__(self, title: str, columns: List[str], data: List[List[Any]] = None):
        super().__init__(title, width=12, height=6)
        self.columns = columns
        self.data = data or []
        self.sortable = True
        self.filterable = True
        self.pagination = {'enabled': True, 'page_size': 10}
    
    def add_row(self, row_data: List[Any]):
        """Add a row to the table."""
        if len(row_data) == len(self.columns):
            self.data.append(row_data)
        else:
            raise ValueError(f"Row data must have {len(self.columns)} columns")
    
    def set_pagination(self, enabled: bool, page_size: int = 10):
        """Configure table pagination."""
        self.pagination = {'enabled': enabled, 'page_size': page_size}
    
    def get_content(self) -> Dict[str, Any]:
        """Get table content for rendering."""
        return {
            'columns': self.columns,
            'data': self.data,
            'sortable': self.sortable,
            'filterable': self.filterable,
            'pagination': self.pagination
        }

class Dashboard:
    """Main dashboard container for organizing widgets."""
    
    def __init__(self, title: str):
        self.title = title
        self.widgets: List[DashboardWidget] = []
        self.layout = "grid"  # grid, flex, custom
        self.theme = "light"
    
    def add_widget(self, widget: DashboardWidget):
        """Add a widget to the dashboard."""
        self.widgets.append(widget)
    
    def remove_widget(self, widget_title: str):
        """Remove a widget by title."""
        self.widgets = [w for w in self.widgets if w.title != widget_title]
    
    def get_widget(self, title: str) -> Optional[DashboardWidget]:
        """Get a widget by title."""
        for widget in self.widgets:
            if widget.title == title:
                return widget
        return None
    
    def render_dashboard(self) -> Dict[str, Any]:
        """Render complete dashboard to JSON."""
        return {
            'title': self.title,
            'layout': self.layout,
            'theme': self.theme,
            'widgets': [widget.render() for widget in self.widgets]
        }

def create_sales_dashboard() -> Dashboard:
    """Factory function to create a sample sales dashboard."""
    dashboard = Dashboard("Sales Analytics")
    
    # Add revenue metric
    revenue_widget = MetricWidget("Monthly Revenue", 125000, "$", "up", 120000)
    revenue_widget.set_format("currency")
    dashboard.add_widget(revenue_widget)
    
    # Add sales chart
    sales_chart = ChartWidget("Sales Trend", "line")
    sales_chart.add_data_point("Jan", 45000)
    sales_chart.add_data_point("Feb", 52000)
    sales_chart.add_data_point("Mar", 48000)
    dashboard.add_widget(sales_chart)
    
    # Add top products table
    products_table = DataTableWidget("Top Products", ["Product", "Sales", "Revenue"])
    products_table.add_row(["Widget A", 150, 15000])
    products_table.add_row(["Widget B", 120, 18000])
    products_table.add_row(["Widget C", 90, 13500])
    dashboard.add_widget(products_table)
    
    return dashboard 