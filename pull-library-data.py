#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import pandas as pd
import altair as alt
import os


# ## Setup API

# In[2]:


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
        if not self.api_from_env:
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
    
    def get_repository(self, repository='Pypi', package='requests'):
        self.url = 'https://libraries.io/api/{}/{}'.format(repository, package)
        self.get_response()
        self.json = self.r.json()
        self.json_flat = self.r.json()
        del self.json_flat['versions']
        del self.json_flat['normalized_licenses']
        del self.json_flat['keywords']
        del self.json_flat['latest_stable_release']
        
        return self.json_flat
    
lib = Libraries(api_from_env=True)
data = lib.get_package(repository='Pypi', package='seaborn')


# In[3]:


lib.json


# # Create csv of data from packages

# In[21]:


packages = [
    ['Pypi', 'seaborn'],
    ['Pypi', 'matplotlib'],
    ['Pypi', 'plotly'],
    ['Pypi', 'bokeh'],
    ['Pypi', 'altair'],
    ['Pypi', 'pygal'],
    ['Pypi', 'geoplotlib'],
    ['Pypi', 'geoplotlib'],


]
lib = Libraries(api_from_env=True)

def make_dataframe(packages, lib):
    package_dict = dict()
    i = 0
    for package in packages:
        package_dict[i] = lib.get_package(repository=package[0], package=package[1])
        i =i+1
    return pd.DataFrame.from_dict(package_dict, orient='index').reindex()
        
df =make_dataframe(packages, lib)
df.to_csv('package-data.csv')
df['1k_stars'] = df['stars']/1000
df['1k_stars'] = df['1k_stars'].astype('int64')


# In[22]:


df


# In[ ]:





# # Create vega-lite visualization using csv

# In[26]:


local = df

alt.Chart(local, width=400, height=400).mark_point().encode(
    x='rank:Q',
    y='1k_stars:Q',
    color='name:N',
    tooltip='name:N',
).interactive()


# In[24]:


url = 'https://raw.githubusercontent.com/library-usage/library-sync/master/package-data.csv'

chart = alt.Chart(url, width=400, height=400).mark_point().encode(
    x='rank:Q',
    y='1k_stars:Q',
    color='name:N',
    tooltip='name:N',
).interactive()
chart


# In[25]:


chart.save('stars.json')


# In[30]:


local = df
alt.Chart(local).transform_window(
    index='count()'
).transform_fold(
    ['dependent_repos_count', 'dependents_count', '1k_stars', 'forks']
).transform_joinaggregate(
     min='min(value)',
     max='max(value)',
     groupby=['key']
).transform_calculate(
    minmax_value=(datum.value-datum.min)/(datum.max-datum.min),
    mid=(datum.min+datum.max)/2
).mark_line().encode(
    x='key:N',
    y='minmax_value:Q',
    color='name:N',
    tooltip='name:N',
#     detail='index:N',
    opacity=alt.value(0.5)
).properties(width=500).interactive()


# In[13]:


url = 'https://raw.githubusercontent.com/library-usage/library-sync/master/package-data.csv'
parallel = alt.Chart(url).transform_window(
    index='count()'
).transform_fold(
    ['dependent_repos_count', 'dependents_count', 'stars', 'forks']
).transform_joinaggregate(
     min='min(value)',
     max='max(value)',
     groupby=['key']
).transform_calculate(
    minmax_value=(datum.value-datum.min)/(datum.max-datum.min),
    mid=(datum.min+datum.max)/2
).mark_line().encode(
    x='key:N',
    y='minmax_value:Q',
    color='name:N',
    tooltip='name:N',
#     detail='index:N',
    opacity=alt.value(0.5)
).properties(width=500).interactive()
parallel


# In[10]:


parallel.save('parallel.json')


# In[11]:


url = 'https://raw.githubusercontent.com/library-usage/library-sync/master/package-data.csv'

parallel = alt.Chart(url, width=400, height=400).mark_point().encode(
    x='rank:Q',
    y='stars:Q',
    color='name:N',
    tooltip='name:N',
).interactive()
chart


# In[ ]:





# In[12]:


get_ipython().system('jupyter nbconvert --to script pull-library-data.ipynb')


# In[ ]:




