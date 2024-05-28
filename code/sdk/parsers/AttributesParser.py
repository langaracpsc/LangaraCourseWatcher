# https://swing.langara.bc.ca/prod/hzgkcald.P_DisplayCatalog
from bs4 import BeautifulSoup, element

from schema.Attribute import Attributes, Attribute

'''
Parses the Langara Course attributes into json
https://swing.langara.bc.ca/prod/hzgkcald.P_DispCrseAttr#A

run with 
s = AttributesParser()
s.LoadParseAndSave()
'''
class AttributesParser:

    def parseHTML(html, attributes:Attributes = Attributes()) -> Attributes:
        
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
        
        
        i = 0
        while i < len(table_items):
            
            
            a = Attribute(
                subject = table_items[i].split(" ")[0],
                course_code = table_items[i].split(" ")[1],
                attributes = {
                    "AR" : table_items[i+1],
                    "SC": table_items[i+2],
                    "HUM": table_items[i+3],
                    "LSC": table_items[i+4],
                    "SCI": table_items[i+5],
                    "SOC": table_items[i+6],
                    "UT": table_items[i+7],  
                 
                },
            )
            
            attributes.addAttribSkipDuplicates(a)
                        
            i += 8
        
        return attributes