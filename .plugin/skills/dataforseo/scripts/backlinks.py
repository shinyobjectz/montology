from client import setup_client
from dataforseo_client.api.backlinks_api import BacklinksApi
from dataforseo_client.models.backlinks_backlinks_live_request_info import BacklinksBacklinksLiveRequestInfo
from dataforseo_client.models.backlinks_summary_live_request_info import BacklinksSummaryLiveRequestInfo
from dataforseo_client.models.backlinks_referring_domains_live_request_info import BacklinksReferringDomainsLiveRequestInfo

def get_backlinks_api():
    api_client = setup_client()
    backlinks_api = BacklinksApi(api_client)
    return backlinks_api

def backlinks(target):
    backlinks_api = get_backlinks_api()
    response = backlinks_api.backlinks_live([BacklinksBacklinksLiveRequestInfo(
        target=target
    )])
    return response

def backlinks_summary(target):
    backlinks_api = get_backlinks_api()
    response = backlinks_api.summary_live([BacklinksSummaryLiveRequestInfo(
        target=target
    )])
    return response

def referring_domains(target):
    backlinks_api = get_backlinks_api()
    response = backlinks_api.referring_domains_live([BacklinksReferringDomainsLiveRequestInfo(
        target=target
    )])
    return response