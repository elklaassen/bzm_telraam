# Import packages
import pandas as pd
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import dash_leaflet as dl
from dash_extensions.javascript import arrow_function, assign


def save_df(df, file_name):
    # Save data frame for debugging purposes
    print('Saving '+ file_name)
    df.to_excel('Data_files/' + file_name + '.xlsx', index=False)


# geojson is loaded from file for performance reasons, could be transfered to pbf someday
# see https://www.dash-leaflet.com/components/vector_layers/geojson

deployed = __name__ != '__main__'
# Initialize the app
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP,dbc_css])
#app = Dash(prevent_initial_callbacks=True)


# Load dummy data
path = 'https://github.com/elklaassen/bzm_telraam/tree/b07edd22f9b340e1af0eff216934c0f7dad7a4ae/Data_files' # Change to your project directory!
# print('Reading file...')
df_sel = pd.read_excel(path+'/bzm_merged_all_test_read.xlsx')

GEO_JSON_NAME = "bzm_telraam_segments.geojson"
#geojson_data = pdg.read_geojson('assets/' + GEO_JSON_NAME)
geojson_url = 'assets/' + GEO_JSON_NAME

# Remove empty rows and set data types
nan_rows = df_sel[df_sel['date_local'].isnull()]
df_sel = df_sel.drop(nan_rows.index)
nan_rows = df_sel[df_sel['osm.name'].isnull()]
df_sel = df_sel.drop(nan_rows.index)

# Add column with selected street and "Other"
def update_sel_street(data_frame, sel_street_name):
    global df_sel_street
    df_sel_street = data_frame
    df_sel_street['street_selection'] = df_sel.loc[:, 'osm.name']
    selection = sel_street_name
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


# geojson_filter = assign("""
#     function(feature, context) {
#         if (feature.properties.cameras.length == 0) return false;
#         const active = feature.properties.uptime === 0;
#         return (active && context.hideout.includes('active')) || (!active && context.hideout.includes('non-active'));
#     }""")

#popup_telraam = assign("""
#    function onEachFeature(feature, layer) {
#        let popupContent = `<a href="https://telraam.net/home/location/${feature.properties.segment_id}">Telraam sensor on segment ${feature.properties.segment_id}</a>`;
#
#        if (feature.properties.last_data_package) {
#            popupContent += `<br/><a href="/csv/segments/bzm_telraam_${feature.properties.segment_id}.csv">CSV data for segment ${feature.properties.segment_id}</a>`;
#        }
#        layer.bindPopup(popupContent);
#   }""")

popup_telraam2 = assign("""
function onEachFeature(feature, layer) {
    layer.on('click', function (e) {
        alert(e.target.feature.properties.osm.name);
        // js2py.eval_js(update_sel_street(df_sel, e.target.feature.properties.osm.name))
        js2py.eval_js(print(e.target.feature.properties.osm.name))
    });
}""")

#options=[{'label': i, 'value': i} for i in df_sel['osm.name'].unique()]
options=[i for i in df_sel['segment_id'].unique()]
#print(options)

#working:
#geojson_filter = assign("""
#            function(feature, context){
#            return ['Kastanienallee','Britzer Damm'].includes(feature.properties.osm.name);
#            }""")
geojson_filter = assign("""
            function(feature, context){
            // alert(typeof feature.properties.segment_id);
            return [9000001661, 9000001786, 9000002074, 9000003790, 9000004035, 9000004065, 9000004597, 9000004669, 9000004995, 9000005444, 9000005484, 9000006435].includes(feature.properties.segment_id);
            }""")
#geojson_filter = assign("""function(feature, context){
#                            document.write(options[1]);
#                            window.alert("option1");
#                        }""")


app.layout = dbc.Container(
    [
        # Main Header
        dbc.Row([
            dbc.Col(
                html.H1('Berlin zählt Mobilität', style={'margin-top': 10,'margin-bottom': 20}), width={'size':12,'offset':0},
            ),
        ]),

        dbc.Row([
            dbc.Col(
                dl.Map(children=[
                    dl.TileLayer(className='dbc'),
                    #dl.GeoJSON(url=('/csv/' if deployed else 'assets/') + GEO_JSON_NAME, id="telraam"), # onEachFeature= popup_telraam2,
                    dl.GeoJSON(url=geojson_url, id="telraam", filter=geojson_filter),
                    html.Div(id="map")
                ], style={'height': '60vh'}, center=(52.5, 13.45), zoom=11),
            width={'size':5, 'offset':0},
            ),
            #dcc.Dropdown(id="dd", options=dd_options, value=dd_defaults, clearable=False, multi=True),

            dbc.Col([
                # General controls: select a street
                html.H3('Select street:', style={'margin-top': 10,'margin-bottom': 10}),

                dcc.Dropdown(id='street_name_dd',
                             options=[{'label': i, 'value': i}
                                      for i in df_sel['osm.name'].unique()],
                             value='Kastanienallee',
                             ),

                # General controls: select a period
                html.H3('Pick date range:', style={'margin-top': 30,'margin-bottom': 10}),
                dcc.DatePickerRange(
                    id="date_filter",
                    start_date=df_sel["date_local"].min(),
                    end_date=df_sel["date_local"].max(),
                    min_date_allowed=df_sel["date_local"].min(),
                    max_date_allowed=df_sel["date_local"].max(),
                    display_format='DD-MMM-YYYY',
                    end_date_placeholder_text='Do-MMMM-YYYY',
                ),
            ], width={'size':3, 'offset':0}),
        ]),

        dbc.Row([
            dbc.Col([
                # Time figures
                html.H3('Total Traffic by:', style={'margin-top': 30,'margin-bottom': 10}),

                # Select a time division
                dcc.RadioItems(id='radio_time_division',
                        options=['year', 'year_month', 'date'],
                        value='year_month',
                        inline=True,
                        ),

                #Show Graphs
                dcc.Graph(id='line_all_traffic', figure={}),
                dcc.Graph(id='hist_car_speed', figure={}),
            ]),
        ]),

        # Averages graphs
        dbc.Row([
            dbc.Col([
                # Select a period
                html.H3('Average Traffic by period:', style={'margin-top': 30,'margin-bottom': 20}),

                dcc.RadioItems(
                    id='time_unit',
                    options=['year', 'month', 'weekday', 'day', 'hour'],
                    value='weekday',
                    inline=True)
            ]),
        ]),

        dbc.Row([
            dbc.Col([
                # Averages figures
                dcc.Graph(id='bar_avg_traffic', figure={}),
                dcc.Graph(id='hist_avg_traffic', figure={})
            ], style={'margin-top': 20, 'margin-bottom': 20}
            ),
        ]),
    ],
    fluid=True,
    className='dbc',
)
@callback(
    Output(component_id='line_all_traffic', component_property='figure'),
    Output(component_id='hist_car_speed', component_property='figure'),
    Input(component_id='telraam', component_property='clickData'),
    Input(component_id='radio_time_division', component_property='value'),
    Input(component_id='street_name_dd', component_property='value'),
    Input(component_id="date_filter", component_property="start_date"),
    Input(component_id="date_filter", component_property="end_date"),
)

def update_graph(feature, radio_time_division, street_name_dd, start_date, end_date):

    # Update selected street based on dd and time period selections
    if feature is not None:
        clickfeatureresult = f"{feature['properties']['osm']['name']}"
        update_sel_street(df_sel, clickfeatureresult)
    else:
        update_sel_street(df_sel, street_name_dd)

    df_sel_street_time = df_sel_street.loc[df_sel_street['date_local'].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]

    # Absolute traffic by time_unit
    df_sel_street_time_agg = df_sel_street_time.groupby(by=[radio_time_division,'street_selection'], as_index=False).agg({'ped_total': 'sum', 'bike_total': 'sum', 'car_total': 'sum', 'heavy_total': 'sum'})
    line_all_traffic = px.line(df_sel_street_time_agg,
                        x=radio_time_division, y=['ped_total', 'bike_total', 'car_total', 'heavy_total'],
                        facet_col='street_selection',
                        facet_col_spacing=0.04,
                        height=600, width=2000,
                        category_orders={'street_selection': ['Other']},
                        title=f'All traffic by {radio_time_division}')

    line_all_traffic.update_layout(yaxis_title = f'Traffic count by {radio_time_division}')
    line_all_traffic.update_yaxes(matches=None)
    line_all_traffic.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
    line_all_traffic.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))

    # Speed up to 50 and 60/70
    add_car_speeding(df_sel_street)
    df_sel_street_speeding_time = df_sel_street_speeding.loc[df_sel_street_speeding['date_local'].between(pd.to_datetime(start_date), pd.to_datetime(end_date))]
    hist_car_speed = px.histogram(df_sel_street_speeding_time,
                        x=radio_time_division, y=['sum_all_speeds','sum_60_70_speeds'],
                        histfunc='avg',
                        facet_col='street_selection',
                        facet_col_spacing=0.04,
                        height=600, width=2000,
                        category_orders={'street_selection': ['Other']},
                        title=f'Car speeding by {radio_time_division}')

    hist_car_speed.update_layout(bargap=0.2)
    hist_car_speed.update_layout(yaxis_title = f'Car speed by {radio_time_division}')
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
                        facet_col_spacing=0.04,
                        height=600, width=2000,
                        category_orders={'street_selection': ['Other']},
                        barmode='stack',
                        title=f'Average traffic by {time_unit}')

    bar_avg_traffic.update_layout(bargap=0.2)
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
                        facet_col_spacing=0.04,
                        height=600, width=2000,
                        category_orders={'street_selection': ['Other']},
                        text_auto=True,
                        title=f'Car speeding % by {time_unit}')

    hist_car_speed_perc.update_layout(bargap=0.2)
    hist_car_speed_perc.update_layout(yaxis_title = f'% Car speed > 50 km/h by {time_unit}')
    hist_car_speed_perc.update_yaxes(matches=None)
    hist_car_speed_perc.update_layout(yaxis_tickformat=".1%")
    hist_car_speed_perc.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
    #hist_car_speed_perc.update_traces(texttemplate="%{y}")
    hist_car_speed_perc.update_traces(textposition='outside')

    return bar_avg_traffic, hist_car_speed_perc

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

