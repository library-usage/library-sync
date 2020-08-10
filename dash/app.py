# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import requests


class Libraries:
    def __init__(self, api_file_path='~/api.txt'):
        self.api_file_path = api_file_path

        self.api_key = None
        self.payload = None
        self.url = None
        self.r = None
        self.json = None
        self.json_flat = None
        #(TODO) self.api_key = "use your own"
        #self.load_api_key()

        return

    def load_api_key(self):
        with open(self.api_file_path, 'r') as file:
            self.api_key = file.read()
        return

    def create_payload(self, paramenters=None):
        self.payload = dict()
        self.payload.update({'api_key': self.api_key})
        return

    def get_response(self):
        self.r = requests.get(self.url, params=self.payload)
        return

    def get_package(self, repository='Pypi', package='requests'):
        self.url = 'https://libraries.io/api/{}/{}'.format(repository, package)
        self.get_response()
        self.json = self.r.json()
        #print(self.r.json())
        self.json_flat = self.r.json()
        del self.json_flat['versions']
        del self.json_flat['normalized_licenses']
        del self.json_flat['keywords']
        del self.json_flat['latest_stable_release']

        return self.json_flat


lib = Libraries()
data = lib.get_package(repository='Pypi', package='numpy')

packages = [
    ['Pypi', 'numpy'],
    ['Pypi', 'requests'],
    ['Pypi', 'plotly'],
    ['Pypi', 'scipy']
]
lib = Libraries()


def make_dataframe(packages, lib):
    package_dict = dict()
    i = 0
    for package in packages:
        package_dict[i] = lib.get_package(repository=package[0], package=package[1])
        i = i + 1
    return pd.DataFrame.from_dict(package_dict, orient='index').reindex()


df = make_dataframe(packages, lib)










external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
#
# df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/5d1ea79569ed194d432e56108a04d188/raw/a9f9e8076b837d541398e999dcbac2b2826a81f8/gdp-life-exp-2007.csv')
#
# fig = px.scatter(df, x="gdp per capita", y="life expectancy",
#                  size="population", color="continent", hover_name="country",
#                  log_x=True, size_max=60)

#df = px.data.iris()
pks_labels = {"name": "dependent_repos_count", "dependents_count": "forks", "rank": "stars", }
fig = px.parallel_coordinates(df, labels=pks_labels,
                              color_continuous_scale=px.colors.diverging.Tealrose,
                              color_continuous_midpoint=2)
app.layout = html.Div([
    dcc.Graph(
        id='life-exp-vs-gdp',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, port=8050)
    #app.run_server(debug=True)
