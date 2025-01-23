
# Shark Watch

This project is a web application built using Python Dash that provides hat visualizes shark-related incidents in Australia. The dashboard provides an interactive, user-friendly tool for the users of the Australian Coast Guard to explore data trends, filter incidents,by date, location, species, victim activities, and other criteria. It also includes features like graph-map, histogram, stacked bar chart and parallel coordinate plots to analyze data trends effectively about sharks' attacks.



## Getting Started
## Features

- **Interactive Map**: Visualize shark incidents geographically, with options for zooming and clicking on specific locations for details.

- **Histogram Analysis**: View distributions of incidents by victim age, state, month, day of the week, and more.

- **Stacked Bar Chart**: Analyze incidents by shark species and provoked/unprovoked incidents.

- **Parallel Coordinates Plot**: Compare numeric variables like distance from shore, incident's depth, total depth and time in water.

- **Date Filtering**: Use of range slider and input boxes, by clicking on the Apply button to filter incidents by date.

- **Colorblind Mode**: A toggle mode with colorblind-friendly palettes for enhanced accessibility.

- **Reset Button**: Resetting the tool to its initial state 

- **Help Modal**: A detailed guide for navigating and using the dashboard.
## Installation

    1) Install my-project with npm

```bash
  git clone https://github.com/DimPap99/JBI100
```
    2) Install the required dependencies:
```bash
  pip install -r requirements.txt
```
    3) Make sure the data file shark.csv is present in the same directory as the project.


## Dependencies

Before installing the program, ensure you have the following:
- **Operating System**: Compatible with Linux, macOS, and Windows (Windows 10 or later recommended).

- **Python**: Python 2.7 or Python 3.5+

- **CSS**: Skeleton Framework V2.0.4

The following Python libraries are required:

    • dash==1.12.0: For building the web application.

    • pandas==0.24.1: For data manipulation and preprocessing.

    • gunicorn==19.9.0: For deploying the application.
## Usage

    1) Run the app
```bash
  python app.py
```
    2) Open your browser and go to http://127.0.0.1:54112/ to access the dashboard.
## License 
Distributed under the Unlicense License. See LICENSE.txt for more information.
## Acknowledgements
Special thanks to the open-source libraries that made this project possible:
 - [Dash Python User Guide](https://dash.plotly.com/)
 - [Google Web Fonts](https://fonts.googleapis.com/css?family=Open+Sans&display=swap)
