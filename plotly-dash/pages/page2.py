import dash
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_html_components as html
import dash_core_components as dcc
from dash_table import DataTable
from plotly.subplots import make_subplots
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
import os.path as osp

from app import app

DATA_DIR = '/Users/eun-yunhye/Developer/scrap/plotly-dash/data'

df = pd.read_csv(osp.join(DATA_DIR, '행정_법정동 중심좌표.csv'), encoding='utf-8')
df = df.drop_duplicates(['시군구', '읍면동'], keep='first')
df_count_region = pd.read_csv(osp.join(DATA_DIR, 'TP_ADSTRD_ACCTO_CARD_USE_FQ.csv'), encoding='utf-8')
df_amount_region = pd.read_csv(osp.join(DATA_DIR, 'TP_LCRCY_SETLE_AMOUNT_CHNGE.csv'), encoding='utf-8')
df_custom = pd.read_csv(osp.join(DATA_DIR, 'custom_dataset_20210417.csv'), encoding='utf-8')
layout = html.Div([
    html.H1('지역별 가맹점 정보'),
    html.Div([
            html.Label([
                '시군구',
                dcc.Dropdown(
                    id='page2-city-dropdown',
                    options= [{'label': x, 'value': x} for x in sorted(list(set(df['시군구'].values)))],
                )
            ], style={'width': '30%'}),
            html.Label([
                '행정동',
                dcc.Dropdown(
                    id='page2-dong-dropdown',
                ),
            ], style={'width': '30%'})
    ], style={'width': '100%', 'display': 'flex', 'margin-top': '20px'}),
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
            html.H2('> 결제 현황'),
            html.Div([
                DataTable(
                    id='page2-table',
                    columns=[
                        {"id": 'gubun', "name": '구분'},
                        {"id": 'region', "name": '지역'},
                        {"id": 'avg', "name": '평균'}
                    ],
                    style_cell={'textAlign': 'center'},
                ),
            ], id='page2-table-div', style={'display': 'None'}),
            # html.H2('> 결제 추이', style={'padding-top': '3%', 'padding-bottom': '3%'}),
            dcc.Graph(id='page2-graph-line', style={'display': 'None'}),
            html.H2('> 업종별 현황', style={'padding-top': '1%'}),
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
    option_list = sorted(list(set(df_custom.loc[df_custom['city'] == city, :]['dong'].values)))
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
    return ' '.join([city, dong]), len(df_custom.loc[(df_custom['city'] == city) & (df_custom['dong'] == dong)])

@app.callback(
    [
        Output(component_id='page2-table', component_property='data'),
        Output(component_id='page2-table-div', component_property='style'),

    ],
    [
        Input(component_id='page2-city-dropdown', component_property='value'),
        Input(component_id='page2-dong-dropdown', component_property='value')
    ]
)

def update_table(city, dong):
    if not city or not dong:
        raise PreventUpdate
    avg_count = int(df_count_region.groupby(['년월']).mean()['사용빈도'].values[-1])
    selected = df_count_region.groupby(['시군구명','동명', '년월']).sum().reset_index()
    region_count = selected.loc[(selected['시군구명'] == city) & (selected['동명'] == dong)]['사용빈도'].values[-1]
    avg_amount = int(df_amount_region.groupby(['일반결제년월']).sum()['결제금액'].values[-1])
    selected = df_amount_region.loc[(df_amount_region['시군구명'] == city) & (df_amount_region['행정동명'] == dong)]
    region_amount = selected['결제금액'].values[-1]
    region_ratio = selected['결제변화비율'].values[-1]
    return [
        {'gubun': '금액', 'region': f'{region_amount} 원', 'avg': f'{avg_amount} 원'},
        {'gubun': '건수', 'region': f'{region_count} 건', 'avg': f'{avg_count} 건'},
        {'gubun': '전월대비', 'region': f'{region_ratio} %', 'avg': '-'}
        ], {}
    
@app.callback(
    [
        Output(component_id="page2-graph-line", component_property="figure"), 
        Output(component_id='page2-graph-line', component_property='style')
    ],
    [
        Input(component_id='page2-city-dropdown', component_property='value'),
        Input(component_id='page2-dong-dropdown', component_property='value')
    ]
)

def make_line_chart(city, dong):
    if not city or not dong:
        raise PreventUpdate
    sample_amount = list(df_amount_region.loc[(df_amount_region['시군구명'] == city) & (df_amount_region['행정동명'] == dong)]['결제금액'].values[1:])
    sample_count = list(df_count_region.loc[(df_count_region['시군구명'] == city) & (df_count_region['동명'] == dong)]['사용빈도'].values)
    sample_date = sorted(list(set(df_count_region['년월'].values)))[1:]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=sample_date, y=sample_amount, name="결제금액"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=sample_date, y=sample_count, name="결제건수"),
        secondary_y=True,
    )
    fig.update_yaxes(title_text="결제금액(원)", secondary_y=False)
    fig.update_yaxes(title_text="결제건수", secondary_y=True)
    fig.update_layout(
        margin=dict(
            t=5
        )
    )
    return fig, {}

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
    sample = df_custom.loc[(df_custom['city'] == city) & (df_custom['dong'] == dong)].groupby('big_category').count().reset_index()
    fig = px.pie(sample, values='name', names='big_category')
    fig.update_layout(
        font=dict(
            size=24,
        )
    )
    return fig, {}


# @app.callback(
#     [
#         Output(component_id='page2-longitude', component_property='children'),
#         Output(component_id='page2-latitude', component_property='children')
#     ],
#     [
#         Input(component_id='page2-city-dropdown', component_property='value'),
#         Input(component_id='page2-dong-dropdown', component_property='value')
#     ]
# )

# def set_center_point(city, dong):
#     if not city or not dong or len(df.loc[(df['시군구'] == city) & (df['읍면동'] == dong), ['경도', '위도']]) == 0:
#         raise PreventUpdate
#     result = df.loc[(df['시군구'] == city) & (df['읍면동'] == dong), ['경도', '위도']]
#     return float(result['경도'].values[0]), float(result['위도'].values[0])

@app.callback(
        Output(component_id='page2-store-list', component_property='children'),
    [
        Input(component_id='page2-city-dropdown', component_property='value'),
        Input(component_id='page2-dong-dropdown', component_property='value')
    ]
)

def update_store_list(city, dong):
    if not city or not dong or len(df_custom.loc[(df_custom['city'] == city) & (df_custom['dong'] == dong)]) == 0:
        raise PreventUpdate
    result = df_custom.loc[(df_custom['city'] == city) & (df_custom['dong'] == dong), :]
    children = []
    for i in range(len(result)):
        t = html.Span(result.iloc[i, 3], className='page2-store-title')
        lat = html.Span(result.iloc[i, 8], className='page2-store-latitude')
        lon = html.Span(result.iloc[i, 9], className='page2-store-longitude')
        ad_road = html.Span(result.iloc[i, 5], className='page2-store-adroad')
        big_category = html.Span(result.iloc[i, 12], className='page2-store-bigcategory')
        category = html.Span(result.iloc[i, 11], className='page2-store-category')
        children.append(html.Div([t, lat, lon, ad_road, big_category, category], className='page2-store'))
    return children