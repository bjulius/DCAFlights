import argparse
import dash
import dash_ag_grid
import dash_design_kit as ddk
import dash_embedded
import datetime
import importlib
import os
import sys
from datetime import datetime

from dash import Dash, html, dcc, Output, Input, State

last_reload = str(datetime.now())

# Initialize the app
app = Dash(
    __name__,
    suppress_callback_exceptions=True,  # Required for dynamic layouts
    plugins=[dash_embedded.Embeddable(origins=["*"], supports_credentials=True)],
)
server = app.server

@app.callback(
    Output("wrapped_app", "children"),
    Output("last_reload", "data"),
    Input("check_for_update", "n_intervals"),
    State("last_reload", "data")
)
def check_for_update(_interval, client_last_reload):
    global last_reload
    if last_reload == client_last_reload:
        return dash.no_update

    return layout(), last_reload

def get_data_layout():
    try:
        from data import get_data
        df = get_data()
    except (ModuleNotFoundError, ImportError):
        return html.Div("Data module not available or still generating...")
    except Exception as e:
        return html.Div(f"Error loading data: {str(e)}")
    # Create a grid component with the dataframe
    grid = dash_ag_grid.AgGrid(
        id="data-grid",
        rowData=df.to_dict("records"),
        columnDefs=[{"field": col} for col in df.columns],
        dashGridOptions={
            "pagination": True,
            "paginationAutoPageSize": True,
        },
        style={"height": "50vh", "width": "100%"},
    )

    # Return a layout with the grid
    return ddk.Card(
        children=[
            grid
        ]
    )


# Define component-specific layout
def get_component_layout(component_id):
    try:
        # Import Filters, if they have finished generating
        from components.filter_component import component as filter_component

        # Get filter with closed state
        filter_instance = filter_component()
        filter_comp = filter_instance["layout"]

        for child in filter_comp._traverse():
            if isinstance(child, ddk._ControlPanel):
                child.default_open = False
                break

    except ModuleNotFoundError:
        filter_comp = None

    try:
        # Dynamically get the specific component
        module_name = "components." + component_id
        component_mod = importlib.import_module(module_name)
        component_func = getattr(component_mod, "component")
        component_instance = component_func()

        # All components now use the new format with layout and test_inputs
        component = component_instance["layout"]

        # Set full width
        component.width = 100

        # Create layout with just filter and component, no header or back link

    except ModuleNotFoundError:
        # Return not found message with minimal UI
        return [
            html.Div("Component not finished generating. It will appear here when it is ready."),
        ]

    return [
        filter_comp,
        component,
    ]


def layout():
    try:
        # Import custom theme, if it exists
        from theme import theme
    except ModuleNotFoundError:
        theme = None

    if component_id == "data":
        children = get_data_layout()
    else:
        children = get_component_layout(component_id)

    return ddk.App(
        children=children,
        theme=theme
    )


def wrapped_layout():

    core_layout = layout()

    hot_reload_components = [
        dcc.Interval(id="check_for_update", interval=2000),
        dcc.Store(id="last_reload", data=last_reload)
    ]

    return html.Div(
        children=[
            html.Div(core_layout, id="wrapped_app"),
            *hot_reload_components,
        ],
    )


app.layout = wrapped_layout

# Run the app
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--component",
        type=str,
        required=True,
        help="Name of the component to preview"
    )

    # Check for command-line component arg
    component_id = None
    for i, arg in enumerate(sys.argv):
        if arg == "--component" and i + 1 < len(sys.argv):
            component_id = sys.argv[i + 1]

            # prevent command injection by requiring the component to be a
            # valid python var name
            assert component_id.isidentifier()
            break

    assert component_id is not None, (
        "A valid component must be specified as a command-line argument")

    print("Starting", component_id, "preview. Press Ctrl+C to stop.")

    # Execute the layout function right away. Component layouts come bundled with
    # callbacks that must be registered before the first request comes in.
    layout()

    # Compute relevant files for hot reloading. We'll prevent all files from
    # hot reloading EXCEPT for these ones:
    include_patterns = [
        "data.py",
        "theme.py",
        "components",
        f"{component_id}.py",
        "filter_component.py"
    ]
    exclude_patterns = os.listdir(".")
    if os.path.isdir("components"):
        exclude_patterns += os.listdir("components")
    exclude_patterns = [f for f in exclude_patterns if f not in include_patterns]

    # Run the app normally
    app.run(
        debug=os.getenv("DASH_DEBUG", "False").lower() in ("true", "1", "yes"),
        use_reloader=True,
        exclude_patterns=exclude_patterns
    )
