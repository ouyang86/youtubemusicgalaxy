#!/usr/bin/env python
# -*- coding: utf-8 -*-

from youtube import *
import sqlite3


#Manipulate SQLite Database using external SQL scripts
def control_db(dbfile, scripts):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    with open(scripts, 'rb') as f:
        rr = f.read()
    try:
        c.executescript(rr)
    except:
        conn.close()
    conn.commit()
    conn.close()

 
#Create a customized generator for reading files
#infile is output of name_title function
def file_generator(infile, fields, process, seperator=u'<SEP>',
                   complete=False, null_str=u'None'):
    with open(infile, 'rb') as f:
        for line in f:
            line = line.decode('utf-8').strip()
            entries = line.split(seperator)
            result = []
            for i, entry in enumerate(entries):
                if i in fields:
                    if i in process:
                        try:
                            func = process[i]
                            entry = func(entry)
                        except:
                            pass
                    if entry == null_str:
                        entry = None
                    result.append(entry)
            if not result:
                continue
            if complete and None in result:
                continue
            if len(result) > 1:
                yield tuple(result)
            else:
                yield result[0]
            
    
    
#Transform a file into a SQL database table
#infile is output of name_title function
def file_to_db(infile, dbfile, table, fields=(0,1,2,3,6), int_ind=(1,),
               seperator=u'<SEP>'):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    arguments = file_generator(infile=infile, fields=fields,
                               int_ind = int_ind, 
                               seperator=seperator)
    placeholder = '('+','.join(['?' for i in range(len(fields))])+')'
    script = ' '.join(['INSERT INTO', table, 'VALUES', placeholder])
    try:
        c.executemany(script, arguments)
    except:
        conn.close()
    conn.commit()
    conn.close()
    
    
#create a customized generator for reading dictionary
#in_dict arguments are output from entity_trend function
def dict_generator(in_dict, key_fields, key_int, value_fields, 
                   value_int, seperator='<SEP>'):
    for key in in_dict:
        entries = key.split(seperator)
        result = []
        for i, entry in enumerate(entries):
            if i in key_fields:
                if i in key_int:
                    try:
                        entry = int(entry)
                    except:
                        pass
                if entry == u'None':
                    entry = None
                result.append(entry)
        for j, value in enumerate(in_dict[key]):
            if j in value_fields:
                if j in value_int:
                    try:
                        value = int(value)
                    except:
                        pass
                if value == u'None':
                    value = None
                result.append(value)
        yield result
        
        
#Transform a dictionary into a SQL database table
def dict_to_db(in_dict, dbfile, table, key_fields=(0,), 
               key_int=(), value_fields=(0,), 
               value_int=(0,), seperator=u'<SEP>'):
    conn = sqlite3.connect(dbfile)
    c = conn.cursor()
    arguments = dict_generator(in_dict=in_dict, 
                               key_fields=key_fields,
                               key_int=key_int, 
                               value_fields=value_fields,
                               value_int=value_int,
                               seperator=seperator)
    arg_length = len(key_fields) + len(value_fields)
    placeholder = '(' + ','.join(['?' for i in xrange(arg_length)]) + ')'
    script = ' '.join(['INSERT INTO', table, 'VALUES', placeholder])
    try:
        c.executemany(script, arguments)
    except:
        conn.close()
    conn.commit()
    conn.close()
    
    
