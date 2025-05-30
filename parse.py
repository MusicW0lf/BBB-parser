import requests

from bs4 import BeautifulSoup
from models import Company
from database_utils import use_db, save_company_to_db
import re
BASE_URL = "https://www.bbb.org"

#find_country = ["US", "CAN"]

headers_initial = {
    "Accept": "application/json, text/plain, */*", 
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "DNT": "1",
    "Host": "www.bbb.org",
    "Sec-GPC": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Referer": "https://www.bbb.org/search",
    "Origin": "https://www.bbb.org",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

headers_extra = {
    "Host": "www.bbb.org",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i"
}



def get_tokens():
    response = requests.get(BASE_URL,headers=headers_extra, stream=True)
    raw_response = response.raw._original_response
    headers = raw_response.getheaders()  # returns list of (header, value)

    for a in headers:
        print(a)
        print("\n")

    # for cookie in response.cookies:
    #     if cookie.name in ("__cf_bm", "CF_Authorization"):
    #         auth_cookies[cookie.name] = cookie.value
    # print(auth_cookies)
    # headers_extra.update(auth_cookies)


def test_token_page():
    get_tokens()
    response = requests.get("https://www.bbb.org/us/ny/new-york/profile/restaurants/cityspree-inc-0121-60114", headers=headers_extra)
    print(response.status_code)

def fetch_initial_info(param_text, page_number):

    params = {
    "find_text": {param_text},
    "find_country": "USA",
    "page": {str(page_number)},
    }

    FETCH_URL = BASE_URL + "/api/search"

    #for testing
    req = requests.Request("GET", FETCH_URL, headers=headers_initial, params=params)
    prepared = req.prepare()
        
    print("Final URL:", prepared.url)
    response = requests.get(FETCH_URL, headers=headers_initial, params=params)

    if response.status_code // 100 == 2 :
        data = response.json()
        
        results = data["results"]

        # testing
        i = 0

        for item in results:
            company = Company(
                company_id=item["id"],
                category=item["tobText"],
                name = re.sub(r"</?em>", "",item["businessName"]),
                phone=item["phone"],
                address=item["address"],
                city=item["city"],
                state=item["state"],
                postalCode=item["postalcode"],
                websiteUrl=None,
                years=None,
                description=None,
                reportUrl=item["localReportUrl"]
            )
            print(f"collected company id: {i}")

            use_db(
                dbname="bbb",
                user="postgres",
                password="postgres",
                callback=lambda cursor, conn: save_company_to_db(cursor, company)
            )
            print(f"saved company id: {i}")
            i+=1
        #print(company)
        #fetch_extra_info(company)


        # item = results
        # for item in results:
        #     company = Company(
        #         company_id=item["id"],
        #         category=item["tobText"],
        #         name=item["businessName"],
        #         phone=item["phone"],
        #         address=item["address"],
        #         city=item["city"],
        #         state=item["state"],
        #         postalCode=item["postalcode"],
        #         websiteUrl=None,
        #         years=None,
        #         description=None,
        #         reportUrl=item["reportUrl"]
        #     )
        #     fetch_extra_info(company)
        #     companies.append(company)
    else:
        print("Problem with response:", response.status_code)
        print(response.text)


def fetch_extra_info(company: Company):
    
    FETCH_URL = BASE_URL + company.reportUrl

    session = requests.Session()
    session.headers.update(headers_extra)
    response = session.get(FETCH_URL)

    print(response.status_code)
    print(response.text[:500])
    if response.status_code // 2:
        print(f"Failed to fetch extra info for {company.name}")
        return {
            "websiteUrl": None,
            "years": None,
            "description": None,
        }

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the <a> tag that has "Visit Website" as its text
    website_link_tag = soup.find("a", string=lambda text: text and "Visit Website" in text)

    website_url = website_link_tag["href"] if website_link_tag else None

    # Placeholder for other values
    years = None
    description = None

    return {
        "websiteUrl": website_url,
        "years": years,
        "description": description,
    }


test_token_page()

# for i in range(15):
#     fetch_initial_info("Restaurants",i+1)