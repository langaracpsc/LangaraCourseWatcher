import requests

nonce = "2acb3bba88"

courses_route = f"https://www.bctransferguide.ca/wp-json/bctg-search/course-to-course/search-from?_wpnonce={nonce}"



headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-CA,en-US;q=0.7,en;q=0.3",
    "Connection": "keep-alive",
    # "Content-Length": "71",
    "Content-Type": "application/x-www-form-urlencoded",
    # "Cookie": "comm100_visitorguid_30000004=43e2385e-2032-4f3a-be6f-f2d2cb239334",
    # "DNT": "1",
    # "Host": "www.bctransferguide.ca",
    # "Origin": "https://www.bctransferguide.ca",
    # "Referer": "https://www.bctransferguide.ca/transfer-options/search-courses/search-course-result/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    # "Cookie" : "comm100_visitorguid_30000004=43e2385e-2032-4f3a-be6f-f2d2cb239334",
    "Sec-GPC": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
}

json = {
    "institutionCode": "LANG",
    "isPublic": None,
    # "pageNumber" : 2,
    "sender": 15,
    "subjectCode": "ABST",
    "subjectId": 504,
}

# # response = requests.post(courses_route,  headers=headers, json=json)

# print(response.json())

print("First response")

pdf_url = f"https://www.bctransferguide.ca/wp-json/bctg-search/course-to-course/search-from/pdf?_wpnonce={nonce}"

response = requests.post(pdf_url, data=json, headers=headers)

with open("file.pdf", "wb") as pdf:
    pdf.write(response.content)

print(response)
# print(response.text)
print()

# print(response.json())