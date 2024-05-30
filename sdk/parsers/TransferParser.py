import pdfquery
import os

from schema.Transfer import Transfer

class TransferParser:
    
    
    # TODO: use PyMuPDF to speed this up   
    def parseTransferPDFs() -> list[Transfer]:
        pdfs = os.listdir("downloads/")
        
        assert len(pdfs) > 0, f"No PDFs to parse in {dir}."
        
        transfers: list[Transfer] = []
                        
        for p in pdfs:

            pdf = pdfquery.PDFQuery("downloads/" + p)
            pdf.load()

            # save xml
            #pdf.tree.write("pain.xml", pretty_print=True)

            pyquery = pdf.pq("LTTextBoxHorizontal")

            stuff:list[str] = []

            for i in pyquery.contents():
                
                # for some reason some elements become lxml.etree._ElementUnicodeResult 
                # and others become pdfquery.pdfquery.LayoutElement
                # ???
                # TODO: make this not terrible
                
                
                try:
                    stuff.append(i.text.strip())
                except:    
                    try:
                        stuff.append(str(i).strip())
                    except:
                        print(f"Could not save {i} {type(i)}")
                        
                # don't save empty ones (idk why there are empty ones)
                # WHY DOESNT THIS WORK
                if stuff[-1].isspace():
                    stuff.pop(-1)

            while "" in stuff:
                stuff.remove("")
                    
            '''
            Remove the following:
            Course Search Result from "Course Loads"
            217 agreements found for 15 courses at 17 institutions
            Generated Apr 9, 2023
            1 of 23
            From
            To
            Transfer Credit
            Effective Date
            '''

            '''
            Parsing something like this:
            LANG ABST 1100
            (there may or may not be a 1 or 2 line description here)
            Credits: 3
            Langara College (BC)
            CAPU
            CAPU HIST 209 (3)
            May/03 to
            present (sometimes present is on the same line as above)
            '''
            print(f"Parsed {p} - {stuff[1]}.")
            #print(stuff[0:50])
            
            # sometimes the 1 of 23 pagecount doesn't show up????
            if "of" in stuff[3]:
                stuff = stuff[8:]
            else:
                stuff = stuff[7:]

            i = 0
            while i < len(stuff):
                
                title = stuff[i].split(" ")
                i += 1
                    
                while "Credits:" not in stuff[i]:
                    description = stuff[i]
                    i += 1
                
                # we don't need the # of credits
                # credit = float(stuff[i].split(":")[-1])
                i += 1
                
                i += 1 # skip Langara College (BC)
                
                dest = stuff[i]
                i += 1
                
                
                #print("Getting transfer info:")
                #print(stuff[i])
                transfer = stuff[i]
                i += 1
                
                while stuff[i][6:9] != " to" or (not stuff[i][4:6].isnumeric() and not stuff[i][3] == "/"):
                    #print(stuff[i])

                    transfer += " " + stuff[i]
                    i += 1
                    
                validity = stuff[i].split("to")
                start = validity[0].strip()
                i += 1
                
                
                if len(validity) == 2 and validity[1] != "":
                    end = validity[1].strip()
                else:
                    # if there is a second line
                    end = stuff[i].strip()
                    i += 1
                    
                    
                transfers.append(Transfer(
                    subject = title[1],
                    course_code = title[2],
                    source=title[0],
                    destination=dest, 
                    credit=transfer,
                    effective_start=start,
                    effective_end=end,
                ))
                
                # why is 8 of 23 here??? what about 1-7 of 23???
                # i don't know why only some of the page numbers show up :sob:
                while i < len(stuff) and " of " in stuff[i]:
                    i += 1
                    
        return transfers
                
