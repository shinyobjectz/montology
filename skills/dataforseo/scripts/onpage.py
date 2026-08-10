from client import setup_client
from dataforseo_client.api.on_page_api import OnPageApi
from dataforseo_client.models.on_page_content_parsing_live_request_info import OnPageContentParsingLiveRequestInfo
from dataforseo_client.models.on_page_instant_pages_request_info import OnPageInstantPagesRequestInfo

def get_onpage_api():
    api_client = setup_client()
    onpage_api = OnPageApi(api_client)
    return onpage_api

def content_parsing(url):
    onpage_api = get_onpage_api()
    response = onpage_api.content_parsing_live([OnPageContentParsingLiveRequestInfo(
        url=url
    )])
    return response

def instant_pages(url):
    onpage_api = get_onpage_api()
    response = onpage_api.instant_pages([OnPageInstantPagesRequestInfo(
        url=url
    )])
    return response