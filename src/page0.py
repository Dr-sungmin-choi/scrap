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

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

pd.set_option('display.float_format', lambda x: '%.0f' % x)

df_lcrcy_induty = pd.read_csv('../data/TP_LCRCY_USE_ND_INDUTY_DISTRB.csv')
df_mwmn = pd.read_csv('../data/TP_MWMN_ACCTO_CNSMP_PTTRN.csv')
df_postnum = pd.read_table('../data/gg.txt', sep='|')
df_postnum = df_postnum.drop(['산여부', '지번본번', '지하여부', '건물번호본번', '건물번호부번', '건물관리번호', '다량배달처명', '시군구용건물명', '읍면동일련번호', '지번부번', '법정동명', '구우편번호', '우편번호일련번호', '도로명코드', '도로명', '도로명영문'], axis=1)
df_postnum = df_postnum.drop_duplicates(['우편번호'], keep='first')
df_1 = df_lcrcy_induty.groupby('가맹점우편번호').sum().reset_index().drop('분석인덱스', axis=1)
df_1_merged = pd.merge(df_1, df_postnum.loc[:, ['우편번호', '시군구', '행정동명']], left_on='가맹점우편번호', right_on='우편번호', how='left').drop('우편번호', axis=1).drop_duplicates(['가맹점우편번호'], keep='first')
dataset = []
dataset.append(df_1_merged.groupby(['시군구', '행정동명']).sum().reset_index())

hovertemplate = []
hovertemplate.append([])
for row in range(len(dataset[0])):
    city = dataset[0].iloc[row, 0]
    dong = dataset[0].iloc[row, 1]
    charge = dataset[0].iloc[row, 3]
    market = dataset[0].iloc[row, 4]
    hovertemplate[0].append(f'{city} {dong}<br>가맹점 수: {market}<br>사용량: {charge}')

app.layout = html.Div([
    html.Div([
        html.H1('LOCAL CURRENCY USAGE', style={'marginBottom': '0'}),
        html.P('행정동별 가맹점수에 따른 지역화폐 사용량', style={'marginTop': '0'}),
        html.Div([
            html.Label([
                '시군구',
                dcc.Dropdown(
                    id='page0-city-dropdown',
                    options= [{'label': x, 'value': x} for x in sorted(list(set(dataset[0]['시군구'].values)))],
                )
            ], style={'width': '50%'}),
            html.Label([
                '행정동',
                dcc.Dropdown(
                    id='page0-dong-dropdown',
                ),
            ], style={'width': '50%'})
        ], style={'width': '100%', 'display': 'inline-block'}),
        html.H3(id='page0-output1', style={'marginBottom': '0'}),
        html.Div([
            dcc.Graph(id='page0-graph1')
        ], style={'width': '100%', 'display': 'inline-block'})
    ], style={'margin': '1%', 'padding': '1% 2%', 'border': '1px solid gray', 'borderRadius': '5px'}),
], style={'padding': '1%'})
    

@app.callback(
    Output(component_id='page0-dong-dropdown', component_property='options'),
    [Input(component_id='page0-city-dropdown', component_property='value')],
)

def update_options(value):
    if not value:
        raise PreventUpdate
    option_list = sorted(list(set(dataset[0].loc[dataset[0]['시군구'] == value, :]['행정동명'].values)))
    result = [{'label': e, 'value': e} for e in option_list]
    return result

@app.callback(
        Output(component_id='page0-output1', component_property='children'),
    [
        Input(component_id='page0-city-dropdown', component_property='value'),
        Input(component_id='page0-dong-dropdown', component_property='value')
    ]
)

def show_output(city, dong):
    if not city or not dong:
        raise PreventUpdate
    result1 = "{} {} 가맹점 수: {} 사용량: {}".format(city, dong,
    dataset[0].loc[(dataset[0]['시군구']==city) & (dataset[0]['행정동명']==dong), :]['상가수'].values[0],
    dataset[0].loc[(dataset[0]['시군구']==city) & (dataset[0]['행정동명']==dong), :]['결제수'].values[0])
    return result1, "현재 설정 지역: {} {}".format(city, dong)

@app.callback(
    Output(component_id='page0-graph1', component_property='figure'),
    [
        Input(component_id='page0-city-dropdown', component_property='value'),
        Input(component_id='page0-dong-dropdown', component_property='value')
    ]
)

def show_graph1(city, dong):
    if not city or not dong:
        raise PreventUpdate

    single = dataset[0].loc[(dataset[0]['시군구']==city) & (dataset[0]['행정동명']==dong), :]
    city = single.iloc[0, 0]
    dong = single.iloc[0, 1]
    charge = single.iloc[0, 3]
    market = single.iloc[0, 4]
    tmp = f'{city} {dong}<br>가맹점 수: {market}<br>사용량: {charge}'
    fig = {
        'data': [
            go.Scatter(
                name='전체',
                x=dataset[0]['상가수'],
                y=dataset[0]['결제수'],
                mode='markers',
                marker={'size': 10,},
                hovertemplate=hovertemplate[0]
            ),
            go.Scatter(
                name='선택',
                x=single['상가수'],
                y=single['결제수'],
                mode='markers',
                marker={'size':15,},
                hovertemplate=tmp
            )
        ],
        'layout':
            go.Layout(
                xaxis={
                    'title': '가맹점 수'
                },
                yaxis={
                    'title': '사용량'
                }
            )
    }
    return fig

if __name__ == "__main__":
    app.run_server(port=8080, debug=True)