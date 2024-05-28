from datetime import datetime
import os
import sqlite3
import time
import gzip
import zlib

from schema.Transfer import Transfer

from scrapers.DownloadTransferInfo import TransferScraper, TransferScraperManager
from scrapers.DownloadLangaraInfo import DownloadAllTermsFromWeb, fetchTermFromWeb

from parsers.AttributesParser import AttributesParser
from parsers.SemesterParser import parseSemesterHTML
from parsers.CatalogueParser import CatalogueParser
from parsers.TransferParser import TransferParser

from schema.Attribute import Attributes
from schema.Catalogue import Catalogue
from schema.Semester import Course, ScheduleEntry, Semester

class Database:
    def __init__(self, database_name="LangaraCourseInfo.db") -> None:
        self.connection = sqlite3.connect(database_name)
        self.cursor = self.connection.cursor()
        
        self.createTables()
    
    def createTables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS TransferInformation(
                subject,
                course_code,
                source,
                destination,
                credit,
                effective_start,
                effective_end,
                PRIMARY KEY (subject, course_code, source, destination, effective_start, effective_end)
                );""")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS CourseInfo(
                subject TEXT,
                course_code INTEGER,
                credits REAL,
                title TEXT,
                description TEXT,
                lecture_hours INTEGER,
                seminar_hours INTEGER,
                lab_hours INTEGER,
                AR bool,
                SC bool,
                HUM bool,
                LSC bool,
                SCI bool,
                SOC bool,
                UT bool,
                PRIMARY KEY (subject, course_code)
            );""")

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Sections(
                year,
                term,
                RP,
                seats,
                waitlist,
                crn,
                subject,
                course_code,
                section,
                credits,
                title,
                additional_fees,
                repeat_limit,
                notes,
                PRIMARY KEY (year, term, crn)
                );""")
        
        # Yes, all those primary keys are neccessary
        # :/
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Schedules(
                year,
                term,
                crn,
                type,
                days,
                time,
                start_date,
                end_date,
                room,
                instructor,
                FOREIGN KEY (year, term, crn) REFERENCES Sections (year, term, crn)
                PRIMARY KEY (year, term, crn, type, days, time, start_date, end_date, room, instructor)
                );""")
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS SemesterHTML(
                year,
                term,
                sectionHTML TEXT,
                catalogueHTML TEXT,
                attributeHTML TEXT,
                PRIMARY KEY (year, term)
            );""")
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS TransferPDF(
                subject TEXT,
                pdf BLOB,
                PRIMARY KEY (subject)
            );""")
        
        
        self.connection.commit()
    
    #def insertMultipleSemesterHTML(self, html:list[tuple[int, int, str]]):
    #    for term in html:
    #        self.insert_SemesterHTML(term[0], term[1], term[2])
    def insertLangaraHTML(self, year:int, term:int, sectionHTML, catalogueHTML, attributeHTML):
        # Compress HTML data
        compressed_section = zlib.compress(sectionHTML.encode())
        compressed_catalogue = zlib.compress(catalogueHTML.encode())
        compressed_attribute = zlib.compress(attributeHTML.encode())
        
        data = (year, term, compressed_section, compressed_catalogue, compressed_attribute)
        self.cursor.execute("INSERT OR REPLACE INTO SemesterHTML VALUES (?, ?, ?, ?, ?)", data)
        self.connection.commit()
        
    def getSemesterHTML(self, year, term) -> tuple[str, str, str]:
        self.cursor.execute("SELECT sectionHTML, catalogueHTML, attributeHTML FROM SemesterHTML WHERE year = ? AND term = ?", (year, term))
        row = self.cursor.fetchone()
        if row:
            # Decompress HTML data
            sectionHTML = zlib.decompress(row[0]).decode()
            catalogueHTML = zlib.decompress(row[1]).decode()
            attributeHTML = zlib.decompress(row[2]).decode()
            return sectionHTML, catalogueHTML, attributeHTML
        return None
    
    def getAllLangaraHTML(self) -> list[tuple[int, int, str, str, str]]:
        self.cursor.execute("SELECT * FROM SemesterHTML ORDER BY year DESC, term DESC")
        rows = self.cursor.fetchall()
        result = []
        for row in rows:
            year, term, compressed_section, compressed_catalogue, compressed_attribute = row
            sectionHTML = zlib.decompress(compressed_section).decode()
            catalogueHTML = zlib.decompress(compressed_catalogue).decode()
            attributeHTML = zlib.decompress(compressed_attribute).decode()
            result.append((year, term, sectionHTML, catalogueHTML, attributeHTML))
        return result
    
    
    def insertSemester(self, semester: Semester):
        section = []
        for c in semester.courses:
            section.append((semester.year, semester.term, c.RP, c.seats, c.waitlist, c.crn, c.subject, c.course_code, c.section, c.credits, c.title, c.add_fees, c.rpt_limit, c.notes))
        
        self.cursor.executemany("INSERT OR REPLACE INTO Sections VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", section)
        self.connection.commit()
        
        
        # Must delete old schedules because sometimes the SIS does that
        delete = []
        for c in semester.courses:
            delete.append((semester.year, semester.term, c.crn))
        self.cursor.executemany("DELETE FROM Schedules WHERE year=? AND term=? AND crn=?", delete)
        self.connection.commit()
        
        # Re add all schedules
        sched = []
        for c in semester.courses:
            for s in c.schedule:
                sched.append((semester.year, semester.term, c.crn, s.type.value, s.days, s.time, s.start, s.end, s.room, s.instructor))
                
        self.cursor.executemany("INSERT OR REPLACE INTO Schedules VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sched)
        self.connection.commit()
    
    def insertCatalogueAttributes(self, catalogue:Catalogue, attributes:Attributes):
        data = []
        for c in catalogue.courses:
            data.append((c.subject, c.course_code, c.credits, c.title, c.description, c.hours["lecture"], c.hours["seminar"], c.hours["lab"]))
        
        a = []
        for c in catalogue.courses:
            a.append(f"{c.subject}{c.course_code}")
        a.sort()
        for i in a:
            pass
            #print(i)
        
        # TODO: fix putting nulls in the database
        self.cursor.executemany("INSERT OR REPLACE INTO CourseInfo VALUES(?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL)", data)
        
        data = []
        for a in attributes.attributes:
            at = a.attributes
            data.append((at["AR"], at["SC"], at["HUM"], at["LSC"], at["SCI"], at["SOC"], at["UT"], a.subject, a.course_code))
        
        self.cursor.executemany("UPDATE CourseInfo SET AR=?, SC=?, HUM=?, LSC=?, SCI=?, SOC=?, UT=? WHERE subject=? AND course_code=?", data)

        self.connection.commit()
    
    def insertTransfers(self, transfers:list[Transfer]):
        data = []
        for t in transfers:
            data.append((t.subject, t.course_code, t.source, t.destination, t.credit, t.effective_start, t.effective_end))
        
        self.cursor.executemany("INSERT OR REPLACE INTO TransferInformation VALUES(?, ?, ?, ?, ?, ?, ?)", data)
        self.connection.commit()
    
    def insertTransferPDF(self, subject, bytes):
        data = (subject, bytes)
        self.cursor.execute("INSERT OR REPLACE INTO TransferPDF VALUES(?, ?)", data)
        self.connection.commit()
    
    def getAllTransferPDF(self) -> list[tuple[str, bytes]]:
        self.cursor.execute("SELECT * FROM TransferPDF")
        return self.cursor.fetchall()
    
    def getSection(self, year, term, crn) -> Course | None:
        c = self.cursor.execute("SELECT * FROM Sections WHERE year=? AND term=? AND crn=?", (year, term, crn))
        c = c.fetchone()
        
        if c is None:
            return None
        
        c = Course(RP=c[2], seats=c[3], waitlist=c[4], crn=c[5], subject=c[6], course_code=c[7], section=c[8], credits=c[9], title=c[10], add_fees=c[11], rpt_limit=c[12], notes=c[13], schedule=[])
        
        c.schedule = self.getSchedules(year, term, c.crn)
        
        assert c.schedule is not None
         
        return c
     
    
    def getSchedules(self, year, term, crn) -> ScheduleEntry | None:
        s_db = self.cursor.execute("SELECT * FROM Schedules WHERE year=? AND term=? AND crn=? ORDER BY type DESC", (year, term, crn))
        s_db = s_db.fetchall()
                        
        if s_db is None:
            return None

        scheds:list[ScheduleEntry] = []
        for s in s_db:
                        
            scheds.append(ScheduleEntry(type=s[3], days=s[4], time=s[5], start=s[6], end=s[7], room=s[8], instructor=s[9]))
        return scheds
    
    




class Utilities():
    def __init__(self, database:Database) -> None:
        self.db = database
        
    # Build Database from scratch, fetching new files from all data sources
    # WARNING: THIS TAKES ~ ONE HOUR TO RUN 
    def buildDatabase(self, skipTransfer=True):
        start = time.time()
        
    
        if not skipTransfer:
            # Download / Save Transfer Information
            # This takes a long time (~1hr) - this will be optimized in the future
            TransferScraperManager.fetch_new_data(self.db)
            TransferScraperManager.sendPDFToDatabase(self.db)
        
        TransferScraperManager.retrieveAllPDFFromDatabase(self.db)
        TransferScraperManager.sendPDFToDatabase(self.db)
        
        # Download and save Langara HTML
        DownloadAllTermsFromWeb(self.db.insertLangaraHTML)

        # Begin parsing saved files
        self.rebuildDatabaseFromStored()
        
        end = time.time()
        hours, rem = divmod(end-start, 3600)
        minutes, seconds = divmod(rem, 60)
        total = "{:0>2}:{:0>2}:{:02d}".format(int(hours),int(minutes),int(seconds))
        print(f"Database built in {total}!")
        
    # Rebuild data by parsing stored HTML and PDF
    # Mostly used for debugging
    # Takes about TEN MINUTES
    def rebuildDatabaseFromStored(self):
        # Clear old data and recreate tables
        self.db.cursor.executescript("DROP TABLE Sections; DROP TABLE Schedules; DROP TABLE CourseInfo; DROP TABLE TransferInformation")
        self.db.connection.commit()
        self.db.createTables()
        
        html = self.db.getAllLangaraHTML()
        
        catalogue = Catalogue()
        attributes = Attributes()
        
        for term in reversed(html):
            print(f"Parsing HTML for {term[0]}{term[1]} ({len(term[2])} chars).")
            
            self.db.insertSemester(parseSemesterHTML(term[2]))
            CatalogueParser.parseCatalogue(term[3], catalogue)
            AttributesParser.parseHTML(term[4], attributes)
        
        #print(catalogue)
        #print(attributes)
        self.db.insertCatalogueAttributes(catalogue, attributes)
        
        # Restore PDF files from database
        TransferScraperManager.retrieveAllPDFFromDatabase(self.db)
        transfers = TransferParser.parseTransferPDFs()
        self.db.insertTransfers(transfers)
        # Delete PDF files from filesystem
        #TransferScraper.sendPDFToDatabase()
    
    def exportDatabase(self, filename_override=None, delete_prev=True):
        
        if filename_override == None:
            t = datetime.today()
            fn = f'LangaraCourseInfo{t.year}{t.month}{t.day}.db'
        else:
            fn = filename_override
            
        
        if delete_prev:
            try:
                os.remove(fn)
            except OSError:
                pass

        new_db = sqlite3.connect(fn)
        # copies all tables
        query = "".join(line for line in self.db.connection.iterdump())
        new_db.executescript(query)

        new_db.executescript("DROP TABLE SemesterHTML; DROP TABLE TransferPDF; VACUUM")
        new_db.commit()
            
            
        
    def countSections(self, year=None, term=None):
        if year != None and term != None:
            query = "SELECT COUNT(*) FROM Sections WHERE year=? AND term=?"
            self.db.cursor.execute(query, (year, term))
        elif year != None:  
            query = "SELECT COUNT(*) FROM Sections WHERE year=?"
            self.db.cursor.execute(query, (year,))
        elif term != None:
            query = "SELECT COUNT(*) FROM Sections WHERE term=?"
            self.db.cursor.execute(query, (term,))
        else:
            self.db.cursor.execute("SELECT COUNT(*) FROM Sections")
        
        result = self.db.cursor.fetchone()
        return result[0]
    
    def databaseSummary(self):
        print("Database information:")
        n = self.db.cursor.execute("SELECT COUNT(*) FROM SemesterHTML").fetchone()
        print(f"{n[0]} semester HTML files found.")
        
        n = self.db.cursor.execute("SELECT COUNT(*) FROM TransferPDF").fetchone()
        print(f"{n[0]} transfer PDF files found.")
        
        n = self.db.cursor.execute("SELECT COUNT(*) FROM CourseInfo").fetchone()
        print(f"{n[0]} unique courses found.")
        
        n = self.db.cursor.execute("SELECT COUNT(*) FROM Sections").fetchone()
        print(f"{n[0]} unique course offerings found.")
        
        n = self.db.cursor.execute("SELECT COUNT(*) FROM Schedules").fetchone()
        print(f"{n[0]} unique schedule entries found.")
        
        n = self.db.cursor.execute("SELECT COUNT(*) FROM TransferInformation").fetchone()
        print(f"{n[0]} unique transfer agreements found.")
    
    def updateCurrentSemester(self) -> list[tuple[Course|None, Course]]:
        
        # Get Last semester.
        yt = self.db.cursor.execute("SELECT year, term FROM Sections ORDER BY year DESC, term DESC").fetchone()
                
        term = fetchTermFromWeb(yt[0], yt[1])
                    
        print(f"Parsing HTML for {term[0]}{term[1]} ({len(term[2])}).")
        semester = parseSemesterHTML(term[2])
        
        # Look for any changes to a course or schedule.
        changes:list[tuple[Course|None, Course]] = []
        
        for c in semester.courses:
            
            # Check if a section with all the same attributes exists in the database.
            db_course:Course = self.db.getSection(semester.year, semester.term, c.crn)

            if db_course == None:
                # This section has not been seen before in the database.
                changes.append((None, c))
                continue
            
            elif not c.isEqual(db_course):
                # This section has different information than in the database.
                changes.append((db_course, c))
                continue
            
            # Look for schedule changes.
            for s in c.schedule:
                
                if not s.isIn(db_course.schedule):
                    # The schedule for this section is different than in the database.
                    changes.append((db_course, c))
                    break
                
        self.db.insertSemester(semester)
        self.db.insertLangaraHTML(term[0], term[1], term[2], term[3], term[4])
        
        c = CatalogueParser.parseCatalogue(term[3])
        a = AttributesParser.parseHTML(term[4])
        self.db.insertCatalogueAttributes(c, a)
        
        return changes
                