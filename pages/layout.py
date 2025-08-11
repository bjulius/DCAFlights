import dash_design_kit as ddk
import datetime
from components.filter_component import component as filter_component
from components.data_cards import component as data_cards_component
from components.data_table import component as data_table_component
from components.delay_by_weekday_bar_chart import component as delay_by_weekday_bar_chart_component
from components.monthly_flight_trends_line_chart import component as monthly_flight_trends_line_chart_component
from components.airline_performance_horizontal_bar import component as airline_performance_horizontal_bar_component
from components.delay_distribution_box_plot import component as delay_distribution_box_plot_component
from components.flight_connections_map import component as flight_connections_map_component
from components.Scatterchart_Showing import component as Scatterchart_Showing_component

def component():
    layout_items = []
    
    # Add hero section
    app_title = "DCA Flight Analysis Data App"
    app_description = "Comprehensive analysis of flight operations from Ronald Reagan Washington National Airport (DCA), examining destinations, delay patterns, seasonal trends, airline performance, and temporal flight patterns to optimize travel planning and understand operational efficiency."
    app_logo = "https://dash.plotly.com/assets/images/plotly_logo_dark.png"
    app_tags = [
        ddk.Tag(text="**Data Updated:** 2025-08-11", icon="circle-check"),
        ddk.Tag(text="**Created by:** Plotly AI Studio", icon="user"),
        ddk.Tag(
            text="**Data Source**: DCA Flight Analysis Data App data",
            icon="database"),
    ]
    layout_items.append(
        ddk.Hero(
            title=app_title,
            description=app_description,
            logo=app_logo,
            tags=app_tags)
    )
    
    # Add filter component
    layout_items.append(filter_component()["layout"])
    
    # Add data cards component
    layout_items.append(data_cards_component()["layout"])
    
    # FIRST ROW: Flight Connections Map (50%) + Airline Performance (50%)
    flight_connections_map_comp = flight_connections_map_component()
    flight_connections_map_layout = flight_connections_map_comp["layout"]
    flight_connections_map_layout.width = 50
    layout_items.append(flight_connections_map_layout)
    
    airline_performance_horizontal_bar_comp = airline_performance_horizontal_bar_component()
    airline_performance_horizontal_bar_layout = airline_performance_horizontal_bar_comp["layout"]
    airline_performance_horizontal_bar_layout.width = 50
    layout_items.append(airline_performance_horizontal_bar_layout)
    
    # SECOND ROW: Monthly Flight Trends (100%)
    monthly_flight_trends_line_chart_comp = monthly_flight_trends_line_chart_component()
    monthly_flight_trends_line_chart_layout = monthly_flight_trends_line_chart_comp["layout"]
    monthly_flight_trends_line_chart_layout.width = 100
    layout_items.append(monthly_flight_trends_line_chart_layout)
    
    # THIRD ROW: Delay by Weekday (50%) + Delay Distribution (50%)
    delay_by_weekday_bar_chart_comp = delay_by_weekday_bar_chart_component()
    delay_by_weekday_bar_chart_layout = delay_by_weekday_bar_chart_comp["layout"]
    delay_by_weekday_bar_chart_layout.width = 50
    layout_items.append(delay_by_weekday_bar_chart_layout)
    
    delay_distribution_box_plot_comp = delay_distribution_box_plot_component()
    delay_distribution_box_plot_layout = delay_distribution_box_plot_comp["layout"]
    delay_distribution_box_plot_layout.width = 50
    layout_items.append(delay_distribution_box_plot_layout)
    
    # FOURTH ROW: Departure vs. Arrival Delay Analysis (100%)
    Scatterchart_Showing_comp = Scatterchart_Showing_component()
    Scatterchart_Showing_layout = Scatterchart_Showing_comp["layout"]
    Scatterchart_Showing_layout.width = 100
    layout_items.append(Scatterchart_Showing_layout)
    
    # FIFTH ROW: Flight Data Table (100%)
    layout_items.append(data_table_component()["layout"])
    
    return layout_items