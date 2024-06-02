# https://swing.langara.bc.ca/prod/hzgkcald.P_DisplayCatalog
from bs4 import BeautifulSoup, element

from sdk.schema.Attribute import AttributeDB

'''
Parses the Langara Course attributes into json
https://swing.langara.bc.ca/prod/hzgkcald.P_DispCrseAttr#A

'''
def parseAttributesHTML(html, year, term) -> list[AttributeDB]:
    
    soup = BeautifulSoup(html, 'lxml')

    # skip the first table which is the form for filtering entries
    table_items:list[element.Tag] = soup.find_all("table")[1].find_all("td")
    
            
    # convert to str, bool, bool, bool, etc
    for i in range(len(table_items)):
        table_items[i] = table_items[i].text
        
        if table_items[i] == "Y":
            table_items[i] = True
        elif table_items[i] == "&nbsp" or table_items[i].isspace():
            table_items[i] = False
    
    attributes: list[AttributeDB] = []
    
    i = 0
    while i < len(table_items):
        
        a = AttributeDB(
            # ATR-year-term-subject-course_code
            id=f"ATR-{year}-{term}-{table_items[i].split(' ')[0]}-{table_items[i].split(' ')[1]}",
            
            subject = table_items[i].split(" ")[0],
            course_code = table_items[i].split(" ")[1],
            attr_ar=table_items[i+1],
            attr_sc=table_items[i+2],
            attr_hum=table_items[i+3],
            attr_lsc=table_items[i+4],
            attr_sci=table_items[i+5],
            attr_soc=table_items[i+6],
            attr_ut=table_items[i+7],
            year=year,
            term=term
        )
        
        attributes.append(a)
                    
        i += 8
    
    return attributes