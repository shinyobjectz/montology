import sys
from dotenv import load_dotenv
import os
from dataforseo_client.rest import ApiException
from labs import *
from onpage import *
from backlinks import *
from serp import *


COMMANDS = {
    "keywords_for_site": keywords_for_site,
    "related_keywords": related_keywords,
    "keyword_suggestions": keyword_suggestions,
    "keyword_ideas": keyword_ideas,
    "bulk_keyword_difficulty": bulk_keyword_difficulty,
    "search_intent": search_intent,
    "keyword_overview": keyword_overview,
    "historical_keyword_data": historical_keyword_data,
    "ranked_keywords": ranked_keywords,
    "bulk_traffic_estimation": bulk_traffic_estimation,

    "content_parsing" : content_parsing,
    "instant_pages": instant_pages,

    "backlinks": backlinks,
    "backlinks_summary": backlinks_summary,
    "referring_domains": referring_domains,

    "google_organic_serp": google_organic_serp,
    "google_news_serp": google_news_serp
}

COMMANDS_WITH_LOC_AND_LANG = [
    "keywords_for_site",
    "related_keywords",
    "keyword_suggestions",
    "keyword_ideas",
    "bulk_keyword_difficulty",
    "search_intent",
    "keyword_overview",
    "historical_keyword_data",
    "ranked_keywords",
    "bulk_traffic_estimation",
    "google_organic_serp",
    "google_news_serp"
]


def main():

    if len(sys.argv) < 3:
        print("Usage: python main.py <command> <arg>")
        return

    command = sys.argv[1]
    arg = sys.argv[2]

    if command not in COMMANDS:
        print("Unknown command")
        return

    func = COMMANDS[command]

    load_dotenv()

    try:
        if command in COMMANDS_WITH_LOC_AND_LANG:
            location = os.getenv("DATAFORSEO_DEFAULT_LOCATION", "United States")
            language = os.getenv("DATAFORSEO_DEFAULT_LANGUAGE", "English")
            result = func(arg, location, language).to_dict()
        else: 
            result = func(arg).to_dict()
    except ApiException as e:
        print("Exception: %s\n" % e)

    print(result)

if __name__ == "__main__":
    main()