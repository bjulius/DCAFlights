# DCA Flights Dashboard

An interactive dashboard for analyzing flight performance data from Ronald Reagan Washington National Airport (DCA).

## Overview

This Dash application provides comprehensive analysis of flight on-time performance, delays, and patterns for flights departing from DCA. The dashboard includes interactive visualizations and filters to explore flight data across multiple dimensions.

## Features

- **Interactive Filters**: Filter by year, airline, destination, time period, and delay categories
- **Key Metrics Cards**: Display total flights, average delays, and on-time performance
- **Multiple Visualizations**:
  - Delay patterns by day of week
  - Monthly flight trends over time
  - Airline performance comparisons
  - Delay distribution analysis
  - Flight connections map
  - Scatter plot analysis with trendlines
- **Data Table**: Detailed flight records with sorting capabilities

## Technology Stack

- **Framework**: Dash 3.2.0
- **Visualization**: Plotly 6.2.0
- **Data Processing**: Pandas 2.3.1, NumPy 2.3.2
- **Components**: 
  - Dash Design Kit (Enterprise)
  - Dash AG Grid
  - PyArrow for data serialization
- **Statistical Analysis**: Statsmodels 0.14.5

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DCAFlights.git
cd DCAFlights
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

Note: This application requires Dash Design Kit and Dash Embedded enterprise packages. Contact Plotly for licensing.

## Usage

Run the application:
```bash
python app.py
```

The dashboard will be available at `http://127.0.0.1:8050/`

## Data

The dashboard uses a dataset of 2,500 simulated flight records from 2019-2024, including:
- Flight details (airline, flight number, destination)
- Scheduled and actual departure/arrival times
- Delay information and categorization
- Distance and time period classifications

## Project Structure

```
DCAFlights/
├── app.py                 # Main application file
├── data.py               # Data loading and processing
├── theme.py              # Visual theme configuration
├── logger.py             # Logging utilities
├── component_preview.py  # Component testing
├── components/           # Dashboard components
│   ├── filter_component.py
│   ├── data_cards.py
│   ├── data_table.py
│   └── ... (various chart components)
├── pages/                # Page layouts
├── data/                 # Data files
├── schema/              # Data schemas
└── requirements.txt     # Python dependencies
```

## Performance Metrics

- **On-Time Performance**: ~87% of flights arrive on time
- **Average Delay**: ~5.6 minutes
- **Data Coverage**: 6 years of flight data
- **Airlines Covered**: Multiple major carriers

## License

This project is available under the MIT License.

## Author

Created by Inspectah DAX (Data Analysis Expert)

## Acknowledgments

- Built with Plotly Enterprise tools
- Flight data simulated based on BTS patterns
- Designed for aviation performance analysis
