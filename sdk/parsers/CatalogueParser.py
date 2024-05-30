from bs4 import BeautifulSoup, element

from sdk.schema.CourseSummary import CourseSummaryDB

'''
Parses the Langara Course Catalogue into json.
https://swing.langara.bc.ca/prod/hzgkcald.P_DisplayCatalog


'''

def parseCatalogueHTML(html, year, term) -> list[CourseSummaryDB] | None:

    try:
        return __parseCatalogueHTML(html, year, term)
    
    except Exception as e:
        # print("Could not parse catalogue:", e)
        return None
        

# This parser has issues and does not work on catalogues before 2012
# probably because catalogues before 2012 have a different format...
def __parseCatalogueHTML(html, year, term) -> list[CourseSummaryDB]:   
    
    summaries: list[CourseSummaryDB] = []     
    
    soup = BeautifulSoup(html, 'lxml')

    coursedivs:list[element.Tag] = soup.find_all("div", class_="course")
    
    
    for div in coursedivs:
        h2 = div.findChild("h2").text
        title = div.findChild("b").text
        
        # the best way i can find to find an element with no tag            
        for e in div.children:
            if not str(e).isspace() and str(e)[0] != "<":
                description = e.text.strip()
                break
        
        h2 = h2.split()
        # h2 = ['ABST', '1100', '(3', 'credits)', '(3:0:0)']
        hours = h2[4].replace("(", "").replace(")", "").split(":")
        hours = {
            "lecture" : float(hours[0]),
            "seminar" : float(hours[1]),
            "lab" :     float(hours[2])
        }

        c = CourseSummaryDB(
            subject=h2[0],
            course_code=int(h2[1]),
            credits=float(h2[2].replace("(", "")),
            hours=hours,
            title=title,
            description=description,
            year=year,
            term=term
        )            
        summaries.append(c)
        
    return summaries