# https://swing.langara.bc.ca/prod/hzgkcald.P_DisplayCatalog
from bs4 import BeautifulSoup, element

from schema.Catalogue import Catalogue, CatalogueCourse


'''
Parses the Langara Course Catalogue into json.
'''
class CatalogueParser:
    
    def parseCatalogue(html, catalogue:Catalogue = Catalogue()) -> Catalogue:
        #return CatalogueParser.__parseCatalogue(html, catalogue)
    
        try:
            return CatalogueParser.__parseCatalogue(html, catalogue)
        except Exception as e:
            print("Could not parse catalogue:", e)
            
    
    # This parser has issues and does not work on catalogues before 2012
    def __parseCatalogue(html, catalogue:Catalogue = Catalogue()) -> Catalogue:        
        
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

            c = CatalogueCourse(
                subject=h2[0],
                course_code=int(h2[1]),
                credits=float(h2[2].replace("(", "")),
                hours=hours,
                title=title,
                description=description,
            )            
            catalogue.addCourseSkipDuplicates(c)
            
        return catalogue