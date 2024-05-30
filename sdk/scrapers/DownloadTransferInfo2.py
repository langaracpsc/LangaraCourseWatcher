import requests






def download_all_subjects(institution="LANG"):
    
    NONCE = ""
    
    
    
    pass

class Subject:
    pass
    

def get_subjects(institution="LANG") :
    
    assert institution == "LANG", "Other institutions are not supported at this time, sorry!"
    InsitutionID = 10020
    
    URL = f"https://ws.bctransferguide.ca/api/custom/ui/v1.7/agreementws/GetSubjects?institutionID={InsitutionID}"
    
    # Their API doesn't like us for some reason
    headers = {
        'Host': 'ws.bctransferguide.ca',
        'User-Agent': 'Wget/1.21.2',
        'Accept': '*/*',
        'Accept-Encoding': 'identity',
        'Connection': 'Keep-Alive'
    }
    
    print(URL)
    
    r = requests.get(URL, headers)
    
    print(r.text)
    

get_subjects()
    
    

def download_subject(subject, institution="LANG"):
    pass

