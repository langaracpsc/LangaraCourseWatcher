import json
import requests
import aiohttp
import asyncio



class TransferScraper:
    
    nonce = "29c6569502" # must figure out how to generate this
    
    headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-CA,en-US;q=0.7,en;q=0.3",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        }

    def get_institution_info(institution_code="LANG") -> dict:
        
        institution_ids_route = f"https://ws.bctransferguide.ca/api/custom/ui/v1.7/agreementws/GetFromInstitutions"

        # params = {"countryId": "BC"}
        response = requests.get(institution_ids_route, headers=TransferScraper.headers)

        institutions = response.json()
        
        institutionInfo = next(filter(lambda i: i["Code"] == institution_code, institutions))
        
        # assert institutionInfo["Title"] == "Langara College"
        assert institutionInfo["Id"] != None
        return institutionInfo
    
    # GET LIST OF ALL SUBJECTS THAT TRANSFER FROM LANGARA
    def get_subjects(institutionInfo:dict) -> list[dict]:
        
        assert institutionInfo["Id"] != None

        subjects_route = f"https://ws.bctransferguide.ca/api/custom/ui/v1.7/agreementws/GetSubjects?institutionID={institutionInfo['Id']}&sending=true"

        response = requests.get(subjects_route, headers=TransferScraper.headers)
        """ This should return a list of subjects
        {
        "IsFPM":false,
        "UrlFPM":"None",
        "InstitutionId":15,
        "Id":505,
        "Code":"ACCT",
        "Title":"Accounting"
        }
        """
                
        subjects_json = response.json()
        assert subjects_json[0]["InstitutionId"] == institutionInfo["Id"]
        
        data:list[dict] = response.json()
        
        for subject in data:
            subject.pop("IsFPM")
            subject.pop("UrlFPM")
            subject.pop("InstitutionId")
            
        return data
    
    @staticmethod
    async def __get_transfer_information(sem, institution_code, subject_info):
        courses_route = f"https://www.bctransferguide.ca/wp-json/bctg-search/course-to-course/search-from?_wpnonce={TransferScraper.nonce}"

        agreements = []
        page = 1
        
        searchstart = False

        while True:
            payload = {
                "institutionCode": institution_code,
                "isPublic": None,
                "pageNumber": page,
                "sender": institution_code,
                "subjectCode": subject_info["Code"],
                "subjectId": subject_info["Id"],
            }

            async with sem, aiohttp.ClientSession() as session:
                async with session.post(courses_route, headers=TransferScraper.headers, json=payload) as response:
                    
                    if searchstart == False:
                        print(f"Started fetching {subject_info['Code']} {subject_info['Title']}.")
                        searchstart = True
                        
                    try:
                        response.raise_for_status()
                        data = await response.json()
                    except aiohttp.ClientResponseError as e:
                        print(f"Error: {e}")
                        content = await response.text()
                        print(f"Response content: {content}")
                        raise

                    for course in data["courses"]:
                        for a in course["agreements"]:
                            new_dict = {
                                "SndrInstitutionCode": a["SndrInstitutionCode"],
                                "SndrInstitutionName": a["SndrInstitutionName"],
                                "SndrSubjectCode": a["SndrSubjectCode"],
                                "SndrCourseNumber": a["SndrCourseNumber"],
                                "SndrCourseTitle": a["SndrCourseTitle"],
                                "RcvrInstitutionCode": a["RcvrInstitutionCode"],
                                "RcvrInstitutionName": a["RcvrInstitutionName"],
                                "Detail": a["Detail"],
                                "Condition": a["Condition"],
                                "StartDate": a["StartDate"],
                                "EndDate": a["EndDate"],
                            }
                            agreements.append(new_dict)

            page += 1

            # print(data["courseDetail"], "-", len(agreements), "/", data["totalAgreements"], "agreements.")

            if page > data["totalPages"]:
                break
        
        print(f"{len(agreements)} agreement(s) found for {subject_info['Code']} {subject_info['Title']}.")

        return agreements

    @staticmethod
    async def __get_all_transfer_information(institution_code, all_subject_info, max_concurrent_requests):
        sem = asyncio.Semaphore(max_concurrent_requests)
        tasks = [TransferScraper.__get_transfer_information(sem, institution_code, subject) for subject in all_subject_info]
        return await asyncio.gather(*tasks)
    
    
    # call with asyncio.run(get_all_transfer_information())
    # takes about 20 minutes
    async def get_all_transfer_information(json_save_location="data/transfers.json"):
        
        institutionInfo = TransferScraper.get_institution_info()
        subjects = TransferScraper.get_subjects(institutionInfo)
        max_concurrent_requests = 10
        
        try:
            results = await TransferScraper.__get_all_transfer_information(
                institutionInfo["Id"], subjects, max_concurrent_requests
            )
            
        except Exception as e:
            print(f"An error occurred: {e}")
            
            with open(json_save_location, "w") as fi:
                fi.write(json.dumps(results))
        
        print(f"Transfer fetching finished. {len(results)} agreements found.")
                
