from client import setup_client
from dataforseo_client.api.dataforseo_labs_api import DataforseoLabsApi
from dataforseo_client.models.dataforseo_labs_google_keyword_ideas_live_request_info import DataforseoLabsGoogleKeywordIdeasLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_related_keywords_live_request_info import DataforseoLabsGoogleRelatedKeywordsLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_keywords_for_site_live_request_info import DataforseoLabsGoogleKeywordsForSiteLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_keyword_suggestions_live_request_info import DataforseoLabsGoogleKeywordSuggestionsLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_bulk_keyword_difficulty_live_request_info import DataforseoLabsGoogleBulkKeywordDifficultyLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_search_intent_live_request_info import DataforseoLabsGoogleSearchIntentLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_keyword_overview_live_request_info import DataforseoLabsGoogleKeywordOverviewLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_historical_keyword_data_live_request_info import DataforseoLabsGoogleHistoricalKeywordDataLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_ranked_keywords_live_request_info import DataforseoLabsGoogleRankedKeywordsLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_bulk_traffic_estimation_live_request_info import DataforseoLabsGoogleBulkTrafficEstimationLiveRequestInfo

def get_labs_api():
    api_client = setup_client()
    labs_api = DataforseoLabsApi(api_client)
    return labs_api

def keywords_for_site(target, location, language):
    labs_api = get_labs_api()
    response = labs_api.google_keywords_for_site_live([DataforseoLabsGoogleKeywordsForSiteLiveRequestInfo(
        target=target,
        location_name=location,
        language_name=language
    )])
    return response

def related_keywords(keyword, location, language):
    labs_api = get_labs_api()
    response = labs_api.google_related_keywords_live([DataforseoLabsGoogleRelatedKeywordsLiveRequestInfo(
        keyword=keyword,
        location_name=location,
        language_name=language
    )])
    return response

def keyword_suggestions(keyword, location, language):
    labs_api = get_labs_api()
    response = labs_api.google_keyword_suggestions_live([DataforseoLabsGoogleKeywordSuggestionsLiveRequestInfo(
        keyword=keyword,
        location_name=location,
        language_name=language
    )])
    return response


def keyword_ideas(keywords, location, language):
    labs_api = get_labs_api()
    response = labs_api.google_keyword_ideas_live([DataforseoLabsGoogleKeywordIdeasLiveRequestInfo(
        keywords=keywords.split(","),
        location_name=location,
        language_name=language
    )])
    return response

def bulk_keyword_difficulty(keywords, location, language):
    labs_api = get_labs_api()
    response = labs_api.google_bulk_keyword_difficulty_live([DataforseoLabsGoogleBulkKeywordDifficultyLiveRequestInfo(
        keywords=keywords.split(","),
        location_name=location,
        language_name=language
    )])
    return response

def search_intent(keywords, location, language):
    labs_api = get_labs_api()
    response = labs_api.google_search_intent_live([DataforseoLabsGoogleSearchIntentLiveRequestInfo(
        keywords=keywords.split(","),
        location_name=location,
        language_name=language
    )])
    return response

def keyword_overview(keywords, location, language):
    labs_api = get_labs_api()
    response = labs_api.google_keyword_overview_live([DataforseoLabsGoogleKeywordOverviewLiveRequestInfo(
        keywords=keywords.split(","),
        location_name=location,
        language_name=language
    )])
    return response

def historical_keyword_data(keywords, location, language):
    labs_api = get_labs_api()
    response = labs_api.google_historical_keyword_data_live([DataforseoLabsGoogleHistoricalKeywordDataLiveRequestInfo(
        keywords=keywords.split(","),
        location_name=location,
        language_name=language
    )])
    return response

def ranked_keywords(target, location, language):
    labs_api = get_labs_api()
    response = labs_api.google_ranked_keywords_live([DataforseoLabsGoogleRankedKeywordsLiveRequestInfo(
        target=target,
        location_name=location,
        language_name=language
    )])
    return response

def bulk_traffic_estimation(keywords, location, language):
    labs_api = get_labs_api()
    response = labs_api.google_bulk_traffic_estimation_live([DataforseoLabsGoogleBulkTrafficEstimationLiveRequestInfo(
        keywords=keywords.split(","),
        location_name=location,
        language_name=language
    )])
    return response