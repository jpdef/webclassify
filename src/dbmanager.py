import sqlite3
import os
import sys
import csv

class Table:
    def __init__(self,tablename,dbman, columns):
        self.columns = columns
        self.tablename =  tablename
        self._construct_queries()
        self.dbman = dbman
    
    def _construct_queries(self):
        names        = ', '.join([ ":"+c['name'] for c in self.columns])
        placeholders = ', '.join([ '?' for x in range(len(self.columns))])
        formatters   = ', '.join([ '%s' for x in range(len(self.columns))])
        self.create_str = "CREATE TABLE %s ("+ formatters  + ")"
        self.insert_str = "INSERT INTO "   + self.tablename + " VALUES ("+ names  + ")"
        self.get_str    = "SELECT * FROM " + self.tablename + " WHERE %s"
        self.get_all_str= "SELECT * FROM " + self.tablename
        self.update_str = "UPDATE " + self.tablename + " SET {} WHERE {}" 
   

    def update(self,values, conditions):
        column_str = ", ".join([k+"=:"+k for k in values.keys()])
        condition_str = " and ".join([k+"=:"+k for k in conditions.keys()])
        query = self.update_str.format( column_str, condition_str) 
        self.dbman.execute(query, {**values,**conditions })
        #self.dbman.con.commit()
   
    def insert(self,row,unique=None):
        if unique is not None:
           filtered_row = {k:v for (k,v) in row.items() if k is not unique} 
           if self.get(filtered_row):
               self.update({unique: row[unique]},filtered_row)
           else: 
               self.dbman.execute(self.insert_str , row)
        else:
            self.dbman.execute(self.insert_str , row)
            #self.dbman.con.commit()


    def get_all(self):
        self.dbman.cur.execute(self.get_all_str)
        data =  self.dbman.cur.fetchall()
        return ( [ dict(zip([c['name'] for c in self.columns],d)) for d in data] )

    def get(self,row):
        column_name = row.keys()
        query = self.get_str % " and ".join([cn+"=:"+cn for cn in column_name])
        self.dbman.execute(query, row )
        return self.dbman.cur.fetchone()

class DBManager:
    def __init__(self):
        #Connect to database
        self.con = sqlite3.connect(os.environ['DATABASEPATH'])
        self.cur = self.con.cursor()
        
        #Set fields
        self.tables = {}
        
       
    def __del__(self):
        self.con.close()

    def create_table(self,tablename,columns):
        self.tables[tablename] = Table(tablename,self,columns)
        try:
            #Make a table
            cstr = self.tables[tablename].create_str
            cmdstr = cstr  % tuple([tablename] + [" ".join([c["name"],c["constraint"]]) for c in columns])
            self.cur.execute(cmdstr)
        except sqlite3.Error as E:
            print("DBManager get sqlite error:" + str(E))

    def execute(self,query,args=None):
        try:
            if args is not None:
                self.cur.execute(query,args)
            else:
                self.cur.execute(query)
        except sqlite3.Error as E:
            print("DBManager get sqlite error:" + str(E))
    
    def load(self,data):
        pass
    
    def tospreadsheet(self,tablename,filename):
        if self.tables[tablename]:
            data = self.get_all(tablename)
            #write to file
            with open(filename, 'w') as csvfile:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for d in data:
                    writer.writerow(d)
        else:
            print("Could not find table in database")
    
    def insert(self,tablename,row,unique=None):
        try:
            with self.con: 
                if tablename in self.tables.keys():
                    self.tables[tablename].insert(row,unique)
                else:
                    print("No such tablename : %s" % tablename)

        except sqlite3.Error as E:
            print("DBManager get sqlite error:" + str(E))

    def get(self,tablename,row):
        try:
           if self.tables[tablename]:
              return self.tables[tablename].get(row)
           else:
              print("No such tablename : %s" % tablename)
        except sqlite3.Error as E:
            print("DBManager get sqlite error:" + str(E))
    
    def get_all(self,tablename):
        try:
           if self.tables[tablename]:
              return self.tables[tablename].get_all()
           else:
              print("No such tablename : %s" % tablename)
        except sqlite3.Error as E:
            print("DBManager get sqlite error:" + str(E))

        
#Tests
if __name__ == "__main__":
    #Do the tests
    dbman = DBManager()
    table_columns = [{ "name" : "id", 
                       "type" : "int",
                       "constraint" : "NOT NULL"}, 
                     { "name" : "category", 
                       "type" : "varchar(255)",
                       "constraint" : ""},
                     { "name" : "desc", 
                       "type" : "varchar(255)",
                       "constraint" : "NOT NULL UNIQUE"}]
 
    dbman.create_table("transactions", table_columns)
    dbman.insert("transactions",{"id" : 3, "category" : "food"       , "desc" : "in-in-out"})
    dbman.insert("transactions",{"id" : 4, "category" : "food"       , "desc" : "in-in-out"},unique="id")
    dbman.insert("transactions",{"id" : 4, "category" : "trans"      , "desc" : "oil"})
    dbman.insert("transactions",{"id" : 5, "category" : "watch"      , "desc" : "expense"})
    dbman.insert("transactions",{"id" : 1, "category" : "utilities"  , "desc" : "PGE"})
    print(dbman.get("transactions",{"category" : "food", "id" : 2}))
    print(dbman.get_all("transactions"))
    dbman.tospreadsheet("transactions",os.path.join(os.path.dirname(os.environ['DATABASEPATH']),"test.csv"))

