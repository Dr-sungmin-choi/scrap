import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from app import app
from pages import page0, page1, page2

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2("경기도", className="display-4", style={'margin-bottom': '0'}),
        html.H2("지역화폐", className="display-4"),
        html.Hr(),
        html.P(
            "경기도 지역화폐 공공데이터 시각화", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink("Overview", href="/", active="exact"),
                dbc.NavLink("City", href="/page-1", active="exact"),
                dbc.NavLink("Kakao Map", href="/page-2", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

@app.callback(
    Output(component_id="page-content", component_property="children"),
    Input(component_id="url", component_property="pathname")
)

def render_page_content(pathname):
    if pathname == "/":
        return page0.layout
    elif pathname == "/page-1":
        return page1.layout
    elif pathname == "/page-2":
        return page2.layout
    # If the user tries to reach a different page, return a 404 message
    else:
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
    )


if __name__ == "__main__":
    app.run_server(port=8080, debug=True)