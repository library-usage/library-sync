import requests
import pandas as pd
import os


class Libraries:
    def __init__(self, api_file_path='./local/api.txt', api_from_env=False):
        
        self.api_file_path = api_file_path
        self.api_from_env = api_from_env
        
        self.api_key = None
        self.payload = None
        self.url = None
        self.r  = None
        self.json = None
        self.json_flat = None
        
        self.load_api_key()
        
        return
    
    def load_api_key(self):
        if self.api_from_env:
            with open(self.api_file_path, 'r') as file:
                self.api_key = file.read()
        else:
            self.api_key = os.environ['API_KEY']
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
        self.json_flat = self.r.json()
        del self.json_flat['versions']
        del self.json_flat['normalized_licenses']
        del self.json_flat['keywords']
        del self.json_flat['latest_stable_release']
        
        return self.json_flat
    
packages = [
    ['Pypi', 'numpy'],
    ['Pypi', 'requests'],
    ['Pypi', 'plotly'],
    ['Pypi', 'scipy'],
    ['Pypi', 'altair']
]
lib = Libraries()

def make_dataframe(packages, lib):
    package_dict = dict()
    i = 0
    for package in packages:
        package_dict[i] = lib.get_package(repository=package[0], package=package[1])
        i =i+1
    return pd.DataFrame.from_dict(package_dict, orient='index').reindex()
        
df =make_dataframe(packages, lib)
df.to_csv('package-data.csv')
