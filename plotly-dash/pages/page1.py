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
import os.path as osp

from app import app

token = 'pk.eyJ1IjoicmxveWh2diIsImEiOiJja244Yjd1aTAwZ25kMnZ0YXF3MGp4cm1zIn0.zd5Pk-iMypa4Xz9BbvztVw'
DATA_DIR = '/Users/eun-yunhye/Developer/scrap/plotly-dash/data'

df = pd.read_csv(osp.join(DATA_DIR, 'custom_dataset.csv'), encoding='utf-8')
df_custom = pd.read_csv(osp.join(DATA_DIR, 'custom_dataset_20210417.csv'), encoding='utf-8')
geojson = json.load(open(osp.join(DATA_DIR, 'SIG_202005/custom_geojson.geojson'), encoding='utf-8'))
candidates = ['결제금액', '결제수']

df_summary = df.describe().iloc[[1, 3, 7], :].reset_index().rename(columns={'index': '항목'})

layout = html.Div([
    html.H1('지역별 지역화폐 사용현황'),
    html.Div([
        html.Div([
            html.H2('전체 개요'),
            dcc.RadioItems(
                id='candidate', 
                options=[{'value': x, 'label': x} 
                        for x in candidates],
                value=candidates[0],
                labelStyle={'display': 'inline-block'}
            ),
            dcc.Graph(id="choropleth", style={'display': 'None'}),
        ], style={'padding': '1%', 'width': '50%'}),
        html.Div([
            html.H2('경기도 전체와 비교하기'),
            html.Label([
                '시군구 선택',
                dcc.Dropdown(
                    id='city-dropdown',
                    options= [{'label': x, 'value': x} for x in sorted(list(set(df['시군구명'].values)))],
                )
            ]),
            html.H3(id='output1'),
            html.Div([
                dcc.Graph(id='page1-graph-category', style={'display': 'None'}),
                html.Div(
                    dcc.Graph(id="bar_sum", style={'display': 'None'}), style={'width': '50%'}
                ),
                html.Div(
                    dcc.Graph(id="bar_cnt", style={'display': 'None'}), style={'width': '50%'}
                )
            ], style={'display': 'flex', 'flexFlow': 'row wrap', 'width': '100%'})
        ], style={'padding': '1%', 'width':  '50%', 'display': 'flex', 'flexFlow': 'column nowrap'})
    ], style={'display': 'flex', 'flexFlow': 'row nowrap'}),

], style={'display': 'flex', 'flexFlow': 'column nowrap', 'padding': '2%', 'border': '1px solid black', 'borderRadius': '5px'})

MAPBOX_API_KEY = 'pk.eyJ1IjoicmxveWh2diIsImEiOiJja244Yjd1aTAwZ25kMnZ0YXF3MGp4cm1zIn0.zd5Pk-iMypa4Xz9BbvztVw'

@app.callback(
    [
        Output("choropleth", "figure"), 
        Output('choropleth', 'style')
    ],
    Input("candidate", "value")
)

def display_choropleth(candidate):
    center = [37.5864315, 127.0462965]
    fig = px.choropleth_mapbox(
        df, geojson=geojson, color=candidate,
        mapbox_style="carto-positron",
        locations="시군구명",
        featureidkey='properties.SIG_KOR_NM',
        center={'lat': center[0], 'lon': center[1]},
        opacity=0.5,
        zoom=7,
    )

    fig.update_layout(
        mapbox_accesstoken=MAPBOX_API_KEY,
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    return fig, {}

@app.callback(
        Output(component_id='output1', component_property='children'),
        Input(component_id='city-dropdown', component_property='value')
)

def display_output(city):
    if not city:
        raise PreventUpdate
    result1 = "{}의 총 결제금액은 {:,}원, 총 결제수는 {:,}원 입니다.".format(city,
    df.loc[df['시군구명']==city, :]['결제금액'].values[0],
    df.loc[df['시군구명']==city, :]['결제수'].values[0])
    return result1

@app.callback(
    [
        Output(component_id="page1-graph-category", component_property="figure"), 
        Output(component_id='page1-graph-category', component_property='style')
    ],
    [
        Input(component_id='city-dropdown', component_property='value'),
    ]
)

def make_pie_chart(city):
    if not city:
        raise PreventUpdate
    sample = df_custom.loc[df_custom['city'] == city].groupby('big_category').count().reset_index()
    fig = px.pie(sample, values='name', names='big_category')
    fig.update_layout(
        font=dict(
            size=24,
        )
    )
    return fig, {}

@app.callback(
    [
        Output(component_id='bar_sum', component_property='figure'),
        Output(component_id='bar_sum', component_property='style'),
        Output(component_id='bar_cnt', component_property='figure'),
        Output(component_id='bar_cnt', component_property='style'),
    ],
        Input(component_id='city-dropdown', component_property='value'),
)

def display_bar(city):
    if not city:
        raise PreventUpdate

    selected = df.loc[df['시군구명']==city, ['결제금액', '결제수']]
    selected = pd.concat([selected, df_summary])
    selected['항목'] = [city, '평균', '최소', '최대']

    tmp = []
    for i in range(len(selected)):
        category = selected.iloc[i, 2]
        v_sum = selected.iloc[i, 0]
        tmp.append(f'항목: {category}<br>결제금액: {v_sum}')

    fig_sum = {
        'data': [
            go.Bar(
                name=f'{city}',
                x=selected['항목'],
                y=selected['결제금액'],
                hovertemplate=tmp,
                marker={
                    'color': selected['결제금액'],
                    'colorscale': 'RdBu'
                }
            ),
        ],
        'layout':
            go.Layout(
                title={
                    'text': '< 결제금액 >',
                    'font': {
                        'size': 18
                    }
                },
            )
    }
    tmp = []
    for i in range(len(selected)):
        category = selected.iloc[i, 2]
        v_cnt = selected.iloc[i, 1]
        tmp.append(f'항목: {category}<br>결제수: {v_cnt}')

    fig_cnt = {
        'data': [
            go.Bar(
                name=f'{city}',
                x=selected['항목'],
                y=selected['결제수'],
                hovertemplate=tmp,
                marker={
                    'color': selected['결제수'],
                    'colorscale': 'RdBu'
                }
            ),
        ],
        'layout':
            go.Layout(
                title={
                    'text': '< 결제수 >',
                    'font': {
                        'size': 18
                    }
                },
            )
    }
    return fig_sum, {}, fig_cnt, {}