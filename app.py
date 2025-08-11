import argparse
import dash_design_kit as ddk
import dash_embedded
import datetime
import sys
import traceback
import os

from dash import Dash, html, dcc, callback, Output, Input

# Import custom theme
from theme import theme

# Import Pages
from pages import layout

# Import Components
from components.filter_component import component as filter_component
from components.data_cards import component as data_cards_component
from components.data_table import component as data_table_component
from components.delay_by_weekday_bar_chart import component as delay_by_weekday_bar_chart_component
from components.monthly_flight_trends_line_chart import component as monthly_flight_trends_line_chart_component
from components.airline_performance_horizontal_bar import component as airline_performance_horizontal_bar_component
from components.delay_distribution_box_plot import component as delay_distribution_box_plot_component
from components.flight_connections_map import component as flight_connections_map_component
from components.Scatterchart_Showing import component as Scatterchart_Showing_component


# Initialize the app
app = Dash(
    __name__,
    suppress_callback_exceptions=True,  # Required for dynamic layouts
    plugins=[dash_embedded.Embeddable(origins=["*"], supports_credentials=True)],
    external_stylesheets=[
        # Add Inter font from Google Fonts
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ]
)
server = app.server

# Create a component registry for mapping URL paths to components
component_registry = {
    'data_cards': data_cards_component,
    'data_table': data_table_component,
    'delay_by_weekday_bar_chart': delay_by_weekday_bar_chart_component,
    'monthly_flight_trends_line_chart': monthly_flight_trends_line_chart_component,
    'airline_performance_horizontal_bar': airline_performance_horizontal_bar_component,
    'delay_distribution_box_plot': delay_distribution_box_plot_component,
    'flight_connections_map': flight_connections_map_component,
    'Scatterchart_Showing': Scatterchart_Showing_component
}

# Define the base layout with URL location and content div
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Define the full data app layout
def get_app_layout():
    return ddk.App(layout.component(), theme=theme, show_editor=False)

# Define component-specific layout
def get_component_layout(component_id):
    if component_id in component_registry:
        # Get the specific component
        component_func = component_registry[component_id]
        component_instance = component_func()

        # All components now use the new format with layout and test_inputs
        component = component_instance["layout"]

        # Set full width
        component.width = 100

        # Get filter with closed state
        filter_instance = filter_component()
        filter_comp = filter_instance["layout"]

        for child in filter_comp._traverse():
            if isinstance(child, ddk._ControlPanel):
                child.default_open = False
                break

        # Create layout with just filter and component, no header or back link
        return ddk.App([
            filter_comp,
            component
        ], theme=theme)
    else:
        # Return not found message with minimal UI
        return ddk.App([
            html.Div("Component Not Found", style={"padding": "20px"})
        ], theme=theme)

# Callback to update page content based on URL
@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
)
def display_page(pathname):
    # Check for command-line component arg
    component_id = None
    for i, arg in enumerate(sys.argv):
        if arg == "--component" and i + 1 < len(sys.argv):
            component_id = sys.argv[i + 1]

            # prevent command injection by requiring the component to be a valid python var name
            assert component_id.isidentifier()
            break

    # If component_id specified via command line, override pathname: this app has been told to render a single component only
    if component_id is not None:
        pathname = "/" + component_id

    if pathname == "/" or pathname == "":
        return get_app_layout()

    # Extract component ID from pathname (remove leading slash)
    component_id = pathname.strip("/")

    if component_id in component_registry:
        return get_component_layout(component_id)
    else:
        # Check if it's a valid component
        return get_app_layout()

# Run the app
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--component",
        type=str,
        required=False,
        help="Name of the component to preview"
    )
    print("Starting 1583bdf2-266d-4965-ad24-506e14d4eb10 data app. Press Ctrl+C to stop.")

    # Set Werkzeug environment variables to only watch .py files
    os.environ["WERKZEUG_RELOADER_TYPE"] = "stat"
    os.environ["WERKZEUG_WATCH_INCLUDE_PATTERNS"] = r"\\.py$"

    # Run the app normally
    app.run(debug=os.getenv("DASH_DEBUG", "True").lower() in ("true", "1", "yes"))
