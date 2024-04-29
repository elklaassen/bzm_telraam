# Import packages
import os
import pandas as pd
import requests
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.express as px
import pandas_geojson as pdg
from bs4 import BeautifulSoup


def save_df(df, file_name):
    # Save data frame for debugging purposes
    print('Saving '+ file_name)
    df.to_excel('Data_files/' + file_name + '.xlsx', index=False)

# Initialize the app
app = Dash(__name__)

# Load data
path = 'D:/OneDrive/PycharmProjects/bzm_telraam/Data_files/'
print('Reading file...')
df_sel = pd.read_excel(path+'bzm_merged_all_test_read.xlsx')

# Remove empty rows and set data types
nan_rows = df_sel[df_sel['date_local'].isnull()]
df_sel = df_sel.drop(nan_rows.index)
nan_rows = df_sel[df_sel['osm.name'].isnull()]
df_sel = df_sel.drop(nan_rows.index)

# Add column with selected street and "Other"
def update_sel_street(data_frame, street_name_dd):
    global df_sel_street
    df_sel_street = data_frame
    df_sel_street['street_selection'] = df_sel.loc[:, 'osm.name']
    selection = street_name_dd
    df_sel_street.loc[df_sel_street['street_selection'] != selection, 'street_selection'] = "Other"

# Add speeding columns
def add_car_speeding(data_frame):
    global df_sel_street_speeding
    pd.options.mode.copy_on_write = True

    # Add a new column with the sum of all speeds 0 - 50 km/h
    cols = ['car_speed0','car_speed10','car_speed20','car_speed30','car_speed40','car_speed50','car_speed60','car_speed70']
    data_frame['sum_all_speeds'] = data_frame[cols].sum(axis=1)

    # Drop rows with zero's
    df_sel_street_speeding = data_frame[data_frame.sum_all_speeds != 0]

    # Add a new column with the sum of speeds > 50 km/h
    cols_60_70 = ['car_speed60','car_speed70']
    df_sel_street_speeding['sum_60_70_speeds'] = df_sel_street_speeding[cols_60_70].sum(axis=1)

    # Needs update: df_sel_street_speeding['perc_speeding'] = df_sel_street_speeding.loc[df_sel_street_speeding['sum_60_70_speeds'].div(df_sel_street_speeding['sum_all_speeds'])]
    # df_sel_street_speeding['perc_speeding'] = df_sel_street_speeding.loc[df_sel_street_speeding['sum_60_70_speeds'].div(df_sel_street_speeding['sum_all_speeds'])]
    df_sel_street_speeding['perc_speeding'] = df_sel_street_speeding['sum_60_70_speeds']/df_sel_street_speeding['sum_all_speeds']


app.layout = html.Div([

    html.Div(children=[
        # Main Header
        html.H1('Berlin zählt Mobilität',
            style={'color': 'black', 'fontSize': 32,'font-weight': 'bold', 'font-family': 'sans-serif'}),
        html.Br(),
        ],
    ),

    # Time graphs
    html.Div(children=[
        # General controls: select a street and a period
        html.H2('Total Traffic Over Time',
                style = {'font-family': 'sans-serif'}),

        html.Br(),
        html.H3('Select street and period:',
                style={'font-family': 'sans-serif'}),

        dcc.Dropdown(id='street_name_dd',
                options=[{'label': i, 'value': i}
                          for i in df_sel['osm.name'].unique()],
                style={'font-family': 'sans-serif', 'width': '50%'},
        value='Kastanienallee'),

        html.Br(),
        html.H3('Pick date range:',
                style = {'font-family': 'sans-serif'}),

        # Select period
        dcc.DatePickerRange(
            id="date_filter",
            start_date=df_sel["date_local"].min(),
            end_date=df_sel["date_local"].max(),
            min_date_allowed=df_sel["date_local"].min(),
            max_date_allowed=df_sel["date_local"].max(),
            display_format= 'DD-MMM-YYYY',
            end_date_placeholder_text='Do-MMMM-YYYY',
            #style = {'font-size': '5px','display': 'inline-block', 'border-radius' : '2px', 'border' : '1px solid #ccc', 'color': '#333', 'border-spacing' : '0', 'border-collapse' :'separate'},
            style={'font-family': 'sans-serif'},
        ),

        html.Div(children=[

            # Select a time division
            html.Br(),
            html.H3('Divide time by:',
                style = {'font-family': 'sans-serif'}),

            dcc.RadioItems(id='time_division',
                    options=['year', 'year_month', 'date'],
                    labelStyle={'display': 'inline-block'},
                    style={'color': 'black', 'fontSize': 14, 'font-weight': 'normal','font-family': 'sans-serif'},
                    value='year_month'),
            ],
        ),

        # Time figures
        dcc.Graph(id='line_all_traffic', figure={}),
        dcc.Graph(id='hist_car_speed', figure={}),

        html.Br(),

        ],
    ),

    # Averages graphs
    html.Div(children=[

        # Select a period
        html.H1('Average Traffic by Time Unit:',
                style={'color': 'black', 'fontSize': 18, 'font-weight': 'bold', 'font-family': 'sans-serif'}),
        html.H1('Select street and period:',
                style={'color': 'black', 'fontSize': 18, 'font-weight': 'normal', 'font-family': 'sans-serif'}),

        dcc.RadioItems(id='time_unit',
            options=['year', 'month', 'weekday', 'day', 'hour'],
            labelStyle={'display': 'inline-block'},
            style={'color': 'black', 'fontSize': 14, 'font-weight': 'normal', 'font-family': 'sans-serif'},
            value='weekday'),
            ],
        ),

    # Averages figures
    dcc.Graph(id='bar_avg_traffic', figure={}),
    dcc.Graph(id='hist_avg_traffic', figure={}),

], style={'marginBottom': 50, 'marginTop': 25}
)

@callback(
    #Output(component_id='output-container-date-picker-range', component_property='children'),
    Output(component_id='line_all_traffic', component_property='figure'),
    Output(component_id='hist_car_speed', component_property='figure'),
    Input(component_id='time_division', component_property='value'),
    Input(component_id='street_name_dd', component_property='value'),
    Input(component_id="date_filter", component_property="start_date"),
    Input(component_id="date_filter", component_property="end_date")
)

def update_graph(time_division, street_name_dd, start_date, end_date):

    # Update selected street based on dd and time period selections
    update_sel_street(df_sel, street_name_dd)
    df_sel_street_time = df_sel_street.loc[df_sel_street['date_local'].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]

    # Absolute traffic by time_unit
    df_sel_street_time_agg = df_sel_street_time.groupby(by=[time_division,'street_selection'], as_index=False).agg({'ped_total': 'sum', 'bike_total': 'sum', 'car_total': 'sum', 'heavy_total': 'sum'})
    line_all_traffic = px.line(df_sel_street_time_agg,
                        x=time_division, y=['ped_total', 'bike_total', 'car_total', 'heavy_total'],
                        facet_col='street_selection',
                        category_orders={'street_selection': ['Other']},
                        #markers='True',
                        title=f'All traffic by {time_division}')

    line_all_traffic.update_layout(yaxis_title = f'Traffic count by {time_division}')
    line_all_traffic.update_yaxes(matches=None)
    line_all_traffic.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
    line_all_traffic.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

    # Speed up to 50 and 60/70
    add_car_speeding(df_sel_street)
    df_sel_street_speeding_time = df_sel_street_speeding.loc[df_sel_street_speeding['date_local'].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]
    hist_car_speed = px.histogram(df_sel_street_speeding_time,
                        x=time_division, y=['sum_all_speeds','sum_60_70_speeds'],
                        histfunc='avg',
                        facet_col='street_selection',
                        category_orders={'street_selection': ['Other']},
                        title=f'Car speeding by {time_division}')

    hist_car_speed.update_layout(bargap=0.1)
    hist_car_speed.update_layout(yaxis_title = f'Car speed by {time_division}')
    hist_car_speed.update_yaxes(matches=None)
    hist_car_speed.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
    hist_car_speed.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

    return line_all_traffic, hist_car_speed

@callback(
    Output(component_id='bar_avg_traffic', component_property='figure'),
    Output(component_id='hist_avg_traffic', component_property='figure'),
    Input(component_id='time_unit', component_property='value'),
    Input(component_id='street_name_dd', component_property='value'),
    Input(component_id="date_filter", component_property="start_date"),
    Input(component_id="date_filter", component_property="end_date")
)

def update_graph(time_unit, street_name_dd, start_date, end_date):

    # Update selected street based on dd selection
    update_sel_street(df_sel, street_name_dd)
    df_sel_street_time = df_sel_street.loc[df_sel_street['date_local'].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]

    # Average traffic by time_unit
    df_sel_street_mean = df_sel_street_time.groupby(by=[time_unit,'street_selection'], as_index=False).agg({'ped_total': 'mean', 'bike_total': 'mean', 'car_total': 'mean', 'heavy_total': 'mean'})

    bar_avg_traffic = px.bar(df_sel_street_mean,
                        x=time_unit, y=['ped_total', 'bike_total', 'car_total', 'heavy_total'],
                        facet_col='street_selection',
                        category_orders={'street_selection': ['Other']},
                        barmode='stack',
                        title=f'Average traffic by {time_unit}')

    bar_avg_traffic.update_layout(yaxis_title = f'Traffic count by {time_unit}')
    bar_avg_traffic.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

    # Speeding %
    add_car_speeding(df_sel_street)
    df_sel_street_speeding_time = df_sel_street_speeding.loc[df_sel_street_speeding['date_local'].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]

    #df_sel_street_speeding = df_sel_street_speeding.groupby(by=['sum_all_speeds','sum_60_70_speeds'], as_index=False).agg({'sum_all_speeds': 'mean', 'sum_60_70_speeds': 'mean'})
    hist_car_speed_perc = px.histogram(df_sel_street_speeding_time,
                        x=time_unit, y=['perc_speeding'],
                        histfunc='avg',
                        facet_col='street_selection',
                        category_orders={'street_selection': ['Other']},
                        title=f'Car speeding % by {time_unit}')

    hist_car_speed_perc.update_layout(bargap=0.1)
    hist_car_speed_perc.update_layout(yaxis_title = f'% Car speed > 50 km/h by {time_unit}')
    hist_car_speed_perc.update_layout(yaxis_tickformat=".1%")
    hist_car_speed_perc.update_yaxes(matches=None)
    hist_car_speed_perc.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
    hist_car_speed_perc.update_traces(texttemplate="%{y}")

    return bar_avg_traffic, hist_car_speed_perc

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

