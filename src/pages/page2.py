import dash
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import json

from app import app

df = pd.read_csv('../data/행정_법정동 중심좌표.csv', encoding='utf-8')
df = df.drop_duplicates(['시군구', '읍면동'], keep='first')

df_custom = pd.read_csv('../data/custom_dataset_20210417.csv', encoding='utf-8')
layout = html.Div([
    html.Div([
            html.Label([
                '시군구',
                dcc.Dropdown(
                    id='page2-city-dropdown',
                    options= [{'label': x, 'value': x} for x in sorted(list(set(df['시군구'].values)))],
                )
            ], style={'width': '50%'}),
            html.Label([
                '행정동',
                dcc.Dropdown(
                    id='page2-dong-dropdown',
                ),
            ], style={'width': '50%'})
    ], style={'width': '100%', 'display': 'inline-block'}),
    html.Div([
        html.Span('경도: '),
        html.Span('126.570667', id='page2-longitude'),
        html.Span(' 위도: '),
        html.Span('33.450701', id='page2-latitude'),
    ], style={'display': 'None'}),
    html.Div([
        html.Div(
            id='page2-map', style={'width': '1080px', 'height': '810px'}
        ),
        html.Div([
            html.H2('> 지역별 분석'),
            html.H1(id='page2-city-output', style={'padding': '1%'}),
            html.H2('> 가맹점 수'),
            html.H1(id='page2-city-count-output', style={'padding': '1%'}),
            html.H2('> 업종별 현황'),
            dcc.Graph(id='page2-graph-category', style={'display': 'None'})
        ], id='page2-summary', style={'display': 'flex', 'flex-flow': 'column nowrap', 'width': '50%', 'padding-left': '2%'}
        )
    ], style={'display': 'flex', 'flex-flow': 'row nowrap', 'paddingTop': '3%'}),
    html.Div(id='page2-store-list', style={'display': 'None'})
], style={'display': 'flex', 'flex-flow': 'column nowrap'})

@app.callback(
    Output(component_id='page2-dong-dropdown', component_property='options'),
    [Input(component_id='page2-city-dropdown', component_property='value')],
)

def update_options(city):
    if not city:
        raise PreventUpdate
    option_list = sorted(list(set(df_custom.loc[df_custom['시군명'] == city, :]['행정동'].values)))
    result = [{'label': e, 'value': e} for e in option_list]
    return result

@app.callback(
    [
        Output(component_id='page2-city-output', component_property='children'),
        Output(component_id='page2-city-count-output', component_property='children'),

    ],
    [
        Input(component_id='page2-city-dropdown', component_property='value'),
        Input(component_id='page2-dong-dropdown', component_property='value')
    ]
)

def show_output(city, dong):
    if not city or not dong:
        raise PreventUpdate
    return ' '.join([city, dong]), len(df_custom.loc[(df_custom['시군명'] == city) & (df_custom['행정동'] == dong)])

@app.callback(
    [
        Output(component_id="page2-graph-category", component_property="figure"), 
        Output(component_id='page2-graph-category', component_property='style')
    ],
    [
        Input(component_id='page2-city-dropdown', component_property='value'),
        Input(component_id='page2-dong-dropdown', component_property='value')
    ]
)

def make_pie_chart(city, dong):
    if not city or not dong:
        raise PreventUpdate
    sample = df_custom.loc[(df_custom['시군명'] == city) & (df_custom['행정동'] == dong)].groupby('big_category').count().reset_index()
    fig = px.pie(sample, values='상호명', names='big_category')
    fig.update_layout(
        font=dict(
            size=24,
        )
    )
    return fig, {}


@app.callback(
    [
        Output(component_id='page2-longitude', component_property='children'),
        Output(component_id='page2-latitude', component_property='children')
    ],
    [
        Input(component_id='page2-city-dropdown', component_property='value'),
        Input(component_id='page2-dong-dropdown', component_property='value')
    ]
)

def set_center_point(city, dong):
    if not city or not dong or len(df.loc[(df['시군구'] == city) & (df['읍면동'] == dong), ['경도', '위도']]) == 0:
        raise PreventUpdate
    result = df.loc[(df['시군구'] == city) & (df['읍면동'] == dong), ['경도', '위도']]
    return float(result['경도'].values[0]), float(result['위도'].values[0])

@app.callback(
        Output(component_id='page2-store-list', component_property='children'),
    [
        Input(component_id='page2-city-dropdown', component_property='value'),
        Input(component_id='page2-dong-dropdown', component_property='value')
    ]
)

def update_store_list(city, dong):
    if not city or not dong or len(df_custom.loc[(df_custom['시군명'] == city) & (df_custom['행정동'] == dong)]) == 0:
        raise PreventUpdate
    result = df_custom.loc[(df_custom['시군명'] == city) & (df_custom['행정동'] == dong), :]
    children = []
    for i in range(len(result)):
        t = html.Span(result.iloc[i, 2], className='page2-store-title')
        lat = html.Span(result.iloc[i, 7], className='page2-store-latitude')
        lon = html.Span(result.iloc[i, 8], className='page2-store-longitude')
        children.append(html.Div([t, lat, lon], className='page2-store'))
    return children