from client import setup_client
from dataforseo_client.api.serp_api import SerpApi
from dataforseo_client.models.serp_google_organic_live_advanced_request_info import SerpGoogleOrganicLiveAdvancedRequestInfo
from dataforseo_client.models.serp_google_news_live_advanced_request_info import SerpGoogleNewsLiveAdvancedRequestInfo

def get_serp_api():
    api_client = setup_client()
    serp_api = SerpApi(api_client)
    return serp_api

def google_organic_serp(keyword, location, language):
    serp_api = get_serp_api()
    response = serp_api.google_organic_live_advanced([SerpGoogleOrganicLiveAdvancedRequestInfo(
        keyword=keyword,
        location_name=location,
        language_name=language
    )])
    return response

def google_news_serp(keyword, location, language):
    serp_api = get_serp_api()
    response = serp_api.google_news_live_advanced([SerpGoogleNewsLiveAdvancedRequestInfo(
        keyword=keyword,
        location_name=location,
        language_name=language
    )])
    return response