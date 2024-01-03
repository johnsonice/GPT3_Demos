# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 10:24:56 2022

@author: DYang
"""

import os 
import re 
import string 
import sys
import time 
import spacy
nlp = spacy.load("en_core_web_sm") 

from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

def filter_by_tag(input_list,prefixes,replace_prefix=False):
    """
    Filter a list of strings, keeping only those that start with any of the given prefixes.
    
    :param strings: List of strings to be filtered.
    :param prefixes: List of prefixes to check against.
    :return
    """
    filtered = []
    for s in input_list:
        for prefix in prefixes:
            if s.startswith(prefix):
                if replace_prefix:
                    s = s.replace(prefix, "", 1)
                filtered.append(s)
                break  # Breaks the inner loop once a matching prefix is found
    return filtered

def iter_block_items(parent):

    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    elif isinstance(parent, _Row):
        parent_elm = parent._tr
    else:
        raise ValueError("something's not right")
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def cleanup_table(doc): 

    text_data = []
    #table_data = []
    for block in iter_block_items(doc):
        #text_data = []
        #print(block.text if isinstance(block, Paragraph) else '<table>')
        try: 
            if isinstance(block, Paragraph):
                text_data.append(block.text)
        except ValueError:
            pass  
        # elif isinstance(block, Table):
        #     for row in block.rows:
        #         row_data = []
        #         for cell in row.cells:
        #             for paragraph in cell.paragraphs:
        #                 row_data.append(paragraph.text)
        #         #print("\t".join(row_data))
        #         table_data.append(row_data)
    
    return text_data
            
            
#capitalize only the first letter and make all other parts unchanged 
#(the built-in function capitalize() lowercases other substrings such as GDP when making the first letter uppercase - not applicable)
def capitalize_strict(t: str):
    
    t_list = [x for x in t]
    
    if len(t_list) == 1:
        t = t_list[0].upper() 
    elif len(t_list) > 1:
        t_list = [t_list[0].upper()] + t_list[1:]
        t = ''.join(t_list) 
    else:
        pass 
    
    return t 

def iscapitalize(t: str):
    
    if not t.isupper():
        
        #remove substrings in uppercase
        t = [x for x in t.split(" ") if not x.isupper()]
        if len(t) != 0:
            t = " ".join(t) 
            
            if t == capitalize_strict(t):
                return True
            else:
                return False
        else:
            return False
    else:
        return False 

#remove uppercased substrings in a string 
def remove_upper(t: str):
    
    if not t.isupper():
        t = [x for x in t.split(" ") if not x.isupper()]
        if len(t) != 0:
            t = " ".join(t)     
    return t


def process_doc(para: str, exclude_list: list):
    
    #para = para.text.strip()
    para = para.strip()
    
    #drop the string if it contains certain substrings (mainly the front page) 
    if any(x in para for x in exclude_list):
        return "" 
    
    #drop the string if it contains only punctuations and numbers
    if all(x in string.punctuation for x in para) | (all(x in string.punctuation or x.isdigit() or x.isspace() for x in para)):
        return ""
    
    #label the date 
    match_date = re.fullmatch(r"^(\b\d{1,2}\D{0,3})?\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?)\D?(\d{1,2}(st|nd|rd|th)?)?(([,.\-\/])\D?)?((19[7-9]\d|2\d{3}))$", para, flags = re.IGNORECASE)   
    #match the chart
    match_chart = re.match(r"^Chart|\s\d{1,2}\.|^\(;hart\s\d{1,2}\.|^Figure\s\d{1,2}\.|^(Table|Text Table|Tabl•)\s\w{1,2}\.", para, flags = re.IGNORECASE)
    
    if len(para.split()) != 0:
        table_regex = [t for t in para.split() if (t.isalpha() == False) & (t.endswith(".") == False | t.endswith(",") == False | t.endswith(")") == False | t.endswith(";") == False) & (t.find("Introduction") == -1)]  
        #number_regex = re.compile(r'\d+?\.\d+|\.\d+|\d+-\d+|\d+/\d+|\d+/|-\d+|\d+|½|¼|¼|⅔|¾/') ## clean up all kinds of numbers
        #n_number = len(number_regex.findall(para))
        if len(table_regex)/len(para.split()) >= 0.5:
            #print(para)
            return ""  
        
        else: 
            #another way to remove strings that contain numbers - threshold: 50 % 
            #number_regex = re.compile(r'\d+?\.\d+|\.\d+|\d+-\d+|\d+/\d+|\d+/|-\d+|\d+|½|¼|¼|⅔|¾/') ## clean up all kinds of numbers
            number_regex = re.compile(r'\d+?\.\d+|\.\d+|\d+-\d+|\d+/\d+|\d+/|-\d+|\d+|½|¼|¼|⅔|¾/')
            n_number = len(number_regex.findall(para))
            if (n_number/len(para.split()) > 0.4) and (match_date == None) and (match_chart == None) and (not para.endswith(".")):
                #print(text)
                return "" 
    
    #label To and From
    match_to = re.match(r"^\b(to)(?=:)", para, flags = re.IGNORECASE)
    match_from = re.match(r"^\b(from)(?=:)", para, flags = re.IGNORECASE)
    #label subject
    match_subject = re.match(r"^\b(Subject)(?=:)", para, flags = re.IGNORECASE)

    if match_date != None:
        para = "<Date>" + para  
            
    elif match_to != None:
        para = "<To>" + para 
            
    elif match_from != None:
        para = "<From>" + para 
            
    elif match_subject != None:
        para = "<Subject>" + para 
        
    else:
        para = para
        
    ## fix spacing
    para = re.sub('\s+', ' ', para)
    ## fix string things
    para = re.sub(r'\uf0b7|\x0c|\xa0',' ',para).strip('\n').strip()  
    
    #drop if the string is too short
    if len([p for p in para]) <= 4:
        return ""
        
    return para 

#remove the content/catalog
def remove_content(text: list):
    
    #find the first occurrence of "content" and the first occurrence of "introduction" or "executive summary" after "content"
    #drop everything in between
    for i, t in enumerate(text):   
        match_content = re.match(r"^Contents|^\nContents", t, flags = re.IGNORECASE)
        if match_content != None:
            #print(t)
            
            #start to search for word "introduction" or "executive summary"
            for j, s in enumerate(text[i+1:i+51]):
                match_intro = re.match(r"\s?Executive Summary$|^Introduction$|^Summary$|^ECONOMIC BACKGROUND$", s, flags = re.IGNORECASE)
                if match_intro != None:
                    text = text[:i] + text[i+j+1:]
                    #print(s)
                    break
    return text


# =============================================================================
# #remove charts or figures or tables
# def remove_figure(text: list):
#     
#     i = 0 
#     #remove charts or figures or tables
#     #find strings start with "Chart. x" and the first folling strings start with "Source" or "Sources" and drop everything in between
#     while i < len(text):
# 
#         t = text[i] 
#         #find the start of the pattern
#         match_chart = re.match(r"^(<\w+>){0,1}(Chart|\(;hart|Figure)\s\d{1,2}(\.|,)|^(<\w+>){0,1}(Table|Text Table|Tabl•)\s\w{1,2}(\.|,)", t, flags = re.IGNORECASE)
#         if match_chart != None:
#             #print(i)          
#             
#             k = 0  #count j
#             #l = 0  #count the number of "valid sentences/strings"
#             for j, s in enumerate(text[i+1:i+31]):
#                 #find the end of the pattern
#                 match_source = re.search(r"\b(Sources|Source|Source■):\s", s, flags = re.IGNORECASE)
#                 match_chart = re.match(r"^(<\w+>){0,1}(Chart|\(;hart|Figure)\s\d{1,2}(\.|,)|^(<\w+>){0,1}(Table|Text Table|Tabl•)\s\w{1,2}(\.|,)", s, flags = re.IGNORECASE)
#                 
#                 if match_source != None:
#                     text = text[:i] + text[i+j+2:]
#                     #print(s) 
#                     break
#                 elif match_chart != None:
#                     del text[i+j+1]
#                     del text[i]
#                     break 
#                 else:
#                     k = k + 1 
#                     
#                 #if the end of the pattern cannot be found within 60 steps, then consider it does not exist, only drop the beginning of the pattern    
#                 if k == 30:
#                     del text[i] 
#                         
#                 elif re.search(r"(:,){0,1}\b(Sources|Source|Source■):\s", t) != None:
#                     del text[i]
#             
#         else:
#             #print("NA") 
#             i = i + 1           
#     
#     return text      
# =============================================================================

#remove charts or figures or tables
def remove_figure(text: list):
    
    i = 0 
    #remove charts or figures or tables
    #find strings start with "Chart. x" and the first folling strings start with "Source" or "Sources" and drop everything in between
    while i < len(text):

        t = text[i] 
        #find the start of the pattern
        match_chart = re.match(r"^(<\w+>){0,1}(Chart|\(;hart|Figure)\s\d{1,2}(\.|,)|^(<\w+>){0,1}(Table|Text Table|Tabl•)\s\w{1,2}(\.|,)", t, flags = re.IGNORECASE)
        if match_chart != None:
            del text[i] 
                        
        elif re.search(r"(:,){0,1}\b(Sources|Source|Source■):\s", t) != None:
            del text[i]
            
        else:
            #print("NA") 
            i = i + 1           
    
    return text                    

#label footnotes
def label_footnote(text: list):
    
    for i, t in enumerate(text):
        #match the beginning of the footnote
        match_footnote = re.match(r"^\b\d{1,2}\s?[A-Z]|^\b\d{1,2}\/\s+[A-Z]|^(l{1,2}|'i_i|'l,.\/|Z|Y|li|Zi|fl|!±J|!V|.!.Q|I{1,2}|i{1,2})\/{0,1}\s+[A-Z]", t)
        match_footnote2 = any(x in [w for w in t][:4] for x in ['/', '*'])
        match_footnote3 = re.match(r"\b(Definition|Definitions|Reporting|Adjusters)(:|/.)\s", t)
        match_footnote4= re.match(r"^(W|Y|V)\s+[A-Z]", t) 
        
        if (match_footnote != None) or (match_footnote2 == True) or (match_footnote3 != None)  or (match_footnote4!= None):
            text[i] = "<Footnote>" + t 
            #if it ends properly 
            if t.endswith(".") and (not any(item in ["Ms.","Mr."] for item in t.split(" ")[-4:])):
                pass
            #otherwise, find out where it ends and combine all strings in between     
            else: 
                j = 1 
                while j <= 8:
                    try:
                        s = text[i+j]
                    except IndexError:
                        pass 
                    if s.startswith("<"):
                        break 
                    elif s.endswith("."):
                        text[i: i+j+1] = [' '.join(text[i: i+j+1])]
                        break 
                    else:
                        j = j + 1 
                        
    return text 

#label titles
def label_title(text: list, title_list: list):
        
    for i, t in enumerate(text):
        
        with_punctuation = (len([x for x in t if x in [",", ".", "?", "!", ":", "<"]]) >= 1) 
        
        if (with_punctuation == True) or ("at" in t): 
            pass 
        
        elif (with_punctuation == False) and(len(t.split(" ")) <= 17) and ('sourc' not in t.lower()): 
            
            if "-" in t: #drop "-" and the immediate word after it 
                temp = re.sub("(\w+[\s]*)-[\s]*\w+", "\\1", t)
            else:
                temp = t 
                
            t_upper = (round(sum(iscapitalize(x) for x in temp.split(" "))/(len(remove_upper(temp).split(" "))),1) >= 0.6)       
            if (temp.isupper() == True or (t_upper == True)):
                text[i] = "<Title>" + t    
        
            elif iscapitalize(temp):
                if any(x for x in title_list if x in temp.lower()):
                    text[i] = "<Title>" + t 
                    
        elif (len(t.split(" ")) <= 20) and (any(x for x in ['approved by', 'prepared by'] if x in t.lower())):
                text[i] = "<Title>" + t 
        
    return text 

#label source
def label_source(text: list):
    
    for i, t in enumerate(text):
        
        match_source = re.search(r"(Sources|Source|Source■|Note):\s*", t)  
        match_source2 = re.match(r"\s*\((.+)\)(\s*\d*)", t, flags = re.IGNORECASE)
        
        cond1 = (match_source != None) or ('imf staff calculation' in t.lower())
        cond2 = (match_source2 != None) and (len(t.split(" ")) <= 10)
        
        if cond1 or cond2: 
            text[i] = "<Source>" + t    
            
        else:
            pass
        
    return text 

#label annex
def label_annex(text: list):
    
    for i, t in enumerate(text):
        
        match_annex = re.match(r"Annex\s*(I|i)*/.\s*\W*", t, flags = re.IGNORECASE)   
        
        if match_annex != None:            
            #t = t.replace("<Title>", "") 
            text[i] = "<Annex>" + t
   
    return text 


#label reference 
def label_reference(text: list):
    
    for i, t in enumerate(text):
        
        match_ref1 = re.search(r"Vol\.\s*\d+", t)   
        match_ref2 = re.search(r"(pp\.|pages)\s*\d+", t)  
        match_ref3 = re.match(r"^[A-Z]([a-z]|\s|,|\.)+.*,\s*(18|19|20)[0-9][0-9][a-z]*,\s*(\“|\"|\”){0,1}[A-Z]", t)   
        
        if  ((match_ref1 != None) or (match_ref2 != None) or (match_ref3 != None) or ("Working Paper" in t)) and ("Attached" not in t):
            
            if t.endswith("."):
                text[i] = "<Ref>" + t
            
            else:
                j = 1
                
                while j <= 5:
                    try:
                        s = text[i+j]
                    except IndexError:
                        pass
                    if s.startswith("<"):
                        break
                    elif s.endswith("."):
                        text[i: i+j+1] = [' '.join(text[i: i+j+1])]
                        break 
                    else:
                        j = j + 1 
    return text

#final step: aggressive sanization 
def label_short_str(text: list):

    for i, t in enumerate(text):
        
        match_end = (t[-1] == "." and t[-2] != ".")
        
        if not t.startswith("<") and len(t.split(" ")) <= 8 and not (match_end == True | t.endswith(":") | t.endswith(";")) and ('but' not in t) and t != capitalize_strict(t):
            text[i] = "<Short>" + t
        
        elif '...' in t and not  t.startswith("<") and len(t.split(" ")) <= 10:
             text[i] = "<Short>" + t    
             
        if len(t.split(" ")) <= 15:
            doc = nlp(t)
            count_noun = 0
            count_verb = 0
            
            for token in doc:
                if token.pos_ in ["NOUN", "PROPN", "PRON"]:
                    count_noun += 1
                elif token.pos_ == "VERB":
                    count_verb += 1
                    
            if count_noun <= 1 and count_verb < 1:
                text[i] = "<Short>" + t 
                
    return text 


#remove "_ " pattern inside a word (and Y at the end of a string)
def clean_underscore(para: str):
    
    match_underscore = re.search(r"\b[a-z]+_\s[a-z]+\b", para, flags = re.IGNORECASE)
    match_Y = re.search(r"Y$", para)
    
    if match_underscore != None: 
        para = re.sub("_\s", "", para)
        
    if match_Y != None:
        para =para[:-2]
    
    return para


#put together complete sentence
def label_para(text: list): 
    
     for i, t in enumerate(text):
         
         match_begin = re.match(r"^[A-Z0-9_À-ÿ\(\'\"]", t) 
         match_end = (t[-1] == "." and t[-2] != ".") #only the last position can be ".". exclude strings ended with "... ..."
         
         if t.startswith("<"):
             text[i] = t
            
         elif (match_begin != None) and (match_end == True or t.endswith(":")): 
             text[i] = "<Para>" + t
         
         elif (match_begin != None) and not (match_end == True or t.endswith(":")): 
             temp = ["<Para>" + t]
             tagged = [] 
             j = 1 
        
            
             while j <= 30:
                 try: 
                     s = text[i+j]
                 except IndexError:
                     pass
                 
                 match_intro = re.match(r"Executive Summary$|Introduction$|Summary$|ECONOMIC BACKGROUND$", s, flags = re.IGNORECASE)

                 if match_intro != None:
                     break 
                 elif s.startswith("<") and match_intro == None: 
                     tagged.append(s) 
                     j = j + 1 
                 elif not (s.endswith(".") or s.endswith(":")):
                     temp.append(s)
                     j = j + 1
                 elif s.endswith(".") or s.endswith(":"):
                     temp.append(s)
                     break 

             text[i: i+j+1] = [' '.join(temp)] + tagged 
                     
     return text 

    
#thorough cleaning
def process_text(text: list, remove_list: list, title_list: list): 
    
    #remove empty strings
    text = [t for t in text if t not in remove_list]
    
    #remove the content/catalog 
    text = remove_content(text)

    #label annex
    text = label_annex(text)
    
    #label reference
    text = label_reference(text)
    
    #add titles
    text = label_title(text, title_list)
    
    #add footnote labels
    text = label_footnote(text)
    
    #remove charts or figures or tables
    text = remove_figure(text)
    
    #label sources and other non-text strings
    text = label_source(text)    
    
    #label short incomplete strings
    text = label_short_str(text)
    
    #put together complete sentence
    text = label_para(text)
    
    #keep only tagged strings 
    text = [x for x in text if x.startswith("<")]
    
    #remove "_ " pattern inside words
    text = [clean_underscore(t) for t in text] 
    
    return text



#limit the runtime 
class Timelimit:
    class TakingTooLong(Exception):
        def __init__(self, limit):
            self.limit = limit
        def __str__(self):
            return f'{self.limit} sec execution time limit exceeded'

    def __init__(self, limit):
        self.limit = limit

    def __enter__(self):
        self.start_time = time.time()
        sys.settrace(self._trace)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.settrace(None)

    def _trace(self, frame, event, arg):
        if event == 'opcode':
            return
        if event == 'return':
            elasped = time.time() - self.start_time
            #print(f'{elasped=:.4f}')
            if elasped > self.limit:
                raise self.TakingTooLong(self.limit)
            return
        if event != 'call':
            return

        func_name = frame.f_code.co_name  # Name of function being called.
        if func_name == 'write':
            return  # Ignore write() calls from printing
        #print('* Call to', func_name)
        return self._trace
    
    

            
def process_doc_txt(file_pth: str, file_name: str, exclude_list: list, remove_list: list, title_list: list, output_path: str):
    
    text = ''
    file_pth=file_pth[0]
    file_name=file_name[0]
    with Timelimit(300):
        try: 
            doc = Document(file_pth) 
            temp = cleanup_table(doc)
            t = [process_doc(p, exclude_list = exclude_list) for p in temp]
            text = process_text(t, remove_list=remove_list, title_list=title_list)
            
            if len(text) == 0:
                status = 'fail'
            else:
                status = 'success'
                
        except Exception:
            if len(text) >= 200:
                status = 'problem but long'
            else:
                status = 'problem and short'
            
    if len([text]) > 0:
        file_name = file_name + '.txt'
        txt_path = os.path.join(output_path, file_name)     
            
        with open(txt_path, 'w', encoding='utf-8') as txt:
            for i in text:
                txt.write("\n".join(map(str, i)))
                txt.close()     
    
    return status             
            