import dash
import dash_bootstrap_components as dbc

external_scripts = [
    {'src': '//dapi.kakao.com/v2/maps/sdk.js?appkey=b859f8af7c28ff0bb477f7ee59c23c06'},
    # {'src': '//dapi.kakao.com/v2/maps/sdk.js?appkey=e5b82cccc5ace94b97f2547768cb6285&libraries=services,clusterer,drawing'}
]
app = dash.Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP], external_scripts=external_scripts, suppress_callback_exceptions=True)
server = app.server