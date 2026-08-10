import os
from dataforseo_client import configuration as dfs_config, api_client as dfs_api_provider

def setup_client():
    login = os.getenv("DATAFORSEO_LOGIN")
    password = os.getenv("DATAFORSEO_PASSWORD")

    if not login or not password:
        raise Exception("Missing DATAFORSEO_LOGIN or DATAFORSEO_PASSWORD")
    
    configuration = dfs_config.Configuration(username=login,password=password)
    api_client = dfs_api_provider.ApiClient(configuration)
    return api_client