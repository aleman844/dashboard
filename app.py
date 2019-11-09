from datetime import datetime as dt
import pandas as pd
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import plotly.express as px
from sqlalchemy import create_engine

#Database connection
engine = create_engine('postgresql://nps_demo_user:Inicio.2019@demonps.ch5nt28naaaf.us-east-2.rds.amazonaws.com/strategy')
sqlquery = "select to_timestamp(\"Entry time\", 'DDTH MON YYYY HH24:MI') as \
 \"Entry time\",\"Number\", \"Trade type\", \"Exposure\",CAST(\"Entry balance\" AS NUMERIC), \
 CAST(\"Exit balance\" AS  NUMERIC), CAST(\"Profit\" AS NUMERIC), CAST(\"Pnl (incl fees)\" AS NUMERIC) ,\"Exchange\", \"Margin\", \
 CAST(\"BTC Price\" AS NUMERIC)   from trades"
df = pd.read_sql(sqlquery, engine.connect())
PAGE_SIZE = 10

#Dash object
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css', ])
#Dassh layout
app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    )]
)
app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            #Exchange selector
                            html.Div(
                                className="two columns",
                                children=[
                                    html.H6("Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['Exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ],
                                style={'padding': '5px!important' }
                            ),
                            #leverage selector
                            html.Div(
                                className="two columns",
                                children=[
                                    html.H6("Leverage",),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['Margin'].unique()
                                        ],
                                        value= df['Margin'].unique().min(),
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ], 
                                style={'padding': '5px!important' }
                            ),
                            #Date Range
                            html.Div(
                                className="three columns",
                                children= [
                                        html.H6("Date Range",),
                                        dcc.DatePickerRange(
                                        id='date-range-select', # The id of the DatePicker, its always very important to set an Id for all our components
                                        start_date=df['Entry time'].min(), # The start_date is going to be the min of Order Date in our dataset
                                        end_date=df['Entry time'].max(),
                                        display_format='YYYY/MMM/DD'
                                        ),

                                ]
                            ),
                            #Strategy returns
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Stgy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            #Market returns
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Mkt Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            #Strategy vs market
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Stgy vs. Mkt', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]                   
                    )
                ]
        ), 
        #Candelstick chart
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                        'data': [],

                     },
                )
            ]    
        ),

        html.Div(
                className="row",
                children=[
                    html.Div(
                        className="six columns",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'Number'},
                                    {'name': 'Trade type', 'id': 'Trade type'},
                                    {'name': 'Exposure', 'id': 'Exposure'},
                                    {'name': 'Entry balance', 'id': 'Entry balance'},
                                    {'name': 'Exit balance', 'id': 'Exit balance'},
                                    {'name': 'Pnl (incl fees)', 'id': 'Pnl (incl fees)'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                                page_current=0,
                                page_size=PAGE_SIZE,
                                page_action='custom'                     
                            )
                        ]
                    ),
                    dcc.Graph(
                        id="pnl-types",
                        className="six columns",
                        figure={}
                    )
                ]
            ),
            html.Div(
                className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns",
                        figure={}
                    ),
                    dcc.Graph(
                        id="balance",
                        className="six columns",
                        figure={}
                    )
                ]
            )
    ])        
])

#******************CALL BACK FUNCTIONS*******************************
#Dates call back function
@app.callback(
    [        
        Output('date-range-select', 'start_date'),
        Output('date-range-select', 'end_date'),
    ], 
    [
        Input('exchange-select', 'value'),
    ]
)
def update_dates(exchange_value):
    return df[df["Exchange"]==exchange_value]["Entry time"].min(),df[df["Exchange"]==exchange_value]["Entry time"].max()


def calc_returns_over_month(dff):
    out = []

    for name, group in dff.groupby('YearMonth'):
        exit_balance = group.head(1)['Exit balance'].values[0]
        entry_balance = group.tail(1)['Entry balance'].values[0]
        monthly_return = (exit_balance*100) / (entry_balance)-100
        out.append({
            'month': name,
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out

def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['BTC Price'].values[0]
    btc_end_value = dff.head(1)['BTC Price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['Exit balance'].values[0]
    end_value = dff.head(1)['Entry balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns


def filter_df(d,m=None, e=None, s_date=None, e_date=None):
    if (s_date==None):
        s_date = pd._libs.tslibs.timestamps.Timestamp(d['Entry time'].min())
    
    if (e_date==None):
        e_date = pd._libs.tslibs.timestamps.Timestamp(d['Entry time'].max())
    
    if (e==None):
        e =list(df['Exchange'].unique())
    else:
        e = [e]
    
    if (m==None):
        m = list(d['Margin'].unique())
    else:
        m= [m]
    
    ret =  d[ (d['Entry time']>=  s_date) & (d['Entry time']<=e_date) & (d['Exchange'].isin(e)) & \
        (d['Margin'].isin(m))  ]
    return ret


#General Call back function
@app.callback(
    [        
        Output('market-returns', 'children'),
        Output('strat-returns', 'children'),
        Output('strat-vs-market', 'children'),
        Output('monthly-chart', 'figure'),
        Output('table', 'data'),
        Output('pnl-types', 'figure'),
        Output('daily-btc', 'figure'),
        Output('balance', 'figure'),
    ], 
    [
        Input('exchange-select', 'value'),
        Input('leverage-select', 'value'),
        Input('date-range-select', 'start_date'),
        Input('date-range-select', 'end_date'),
        Input('table', "page_current"),
        Input('table', "page_size")
    ]
)
def udate_graphs(exchange_value, leverage_value, s_date_value, e_date_value, p_c, p_s):
    #Filter data
    df_temp = filter_df(df, e=exchange_value, m=leverage_value, s_date=s_date_value, e_date=e_date_value )
    df_temp['YearMonth'] =  df_temp['Entry time'].dt.strftime('%y-%m')

    #Calc returns
    btc_returns = calc_btc_returns(df_temp)
    strat_returns = calc_strat_returns(df_temp)
    strat_vs_market = strat_returns - btc_returns

    #Candelstick data
    df_agg_month = df_temp.groupby('YearMonth').agg({'Entry balance': 'first', \
        'Exit balance': 'last', 'Pnl (incl fees)': 'sum'}).reset_index()
    data_candlestick  = [ go.Candlestick(
        high = df_agg_month['Exit balance'],
        open = df_agg_month['Exit balance'],
        close = df_agg_month['Entry balance'],
        low =df_agg_month['Entry balance'],
        x = df_agg_month['YearMonth'],
        increasing_line_color='blue',
        decreasing_line_color='red',
    )]

    #Bar plot
    dict_var = []
    for tad in  df_temp['Trade type'].unique():
        dict_var.append({'x':list(df_temp[df_temp['Trade type']==tad]['YearMonth']), \
            'y': list(df_temp[df_temp['Trade type']==tad]['Pnl (incl fees)']), \
                'type': 'bar', 'name': tad})
    data_barplot = dict_var

    #Line btc plot
    trace_btc = go.Scatter(
        x = df_temp['Entry time'],
        y = df_temp['BTC Price'],
        mode='lines'
    )
    data_btc = [trace_btc]

    #Line balance plot
    trace_balance  = go.Scatter(
            x = df_temp['Entry time'],
            y = df_temp['Exit balance'],
            mode='lines'
        )
    data_balance = [trace_balance]
    
    return f'{btc_returns:0.2f}%',f'{strat_returns:0.2f}%' ,f'{strat_vs_market:0.2f}%', \
         {'data': data_candlestick ,'layout': {'title': 'Overview on Monthly Perfomance'}}, \
             df_temp.iloc[p_c*p_s:(p_c+ 1)*p_s].to_dict('records'), \
                 {'data': data_barplot , 'layout': {'title': 'PnL vs Trade Type'}},  \
                     {'data': data_btc ,'layout': {'title': 'Overview on Monthly Perfomance'}},\
                         {'data': data_balance ,'layout': {'title': 'Balance over time'}}

if __name__ == "__main__":
    #app.run_server(debug=True)
    app.run_server(debug=True, host="0.0.0.0", port="8080")


