### extract ram table from AIVs 
#%%
import PyPDF2
import re
#%%
# Save the resulting PDF to a file.
def get_page(filename,page_num):
    pdfFileObj = open(filename,'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    pageObj = pdfReader.getPage(page_num)
    content = pageObj.extract_text().lower().replace('\n','').replace('  ',' ')
    pdfFileObj.close()
    return content

def key_reg_match(content,reg_text=None,search_text=None,mode='all'):
    """use either regular expressions or keywords matching"""
    if reg_text:
        if mode in ['all','rgx']:
            result = reg_text.findall(content)
            if len(result)>0:
                return True
            
    if search_text:
        if mode in ['all','key']:
            if search_text in content:
                return True
    ## if nothing matched     
    return None

#filename = 'U:/STA/documents/Bangladesh 2017.pdf'
#search_text = 'table of common indicators'# required for surveillance'
def get_target_pagenum(filename,match_func,return_mode='first'): ## mode = first or all
    pdfFileObj = open(filename,'rb')
    pdfReader = PyPDF2.PdfReader(pdfFileObj)
    all_res = [] 
    for pageNum in range(len(pdfReader.pages)):
            pageObj = pdfReader.pages[pageNum]
            content = pageObj.extract_text().lower().replace('\n','').replace('  ',' ')
            match_result = match_func(content)
            if match_result:
                if return_mode=='first':
                    pdfFileObj.close()
                    return pageNum
                if return_mode=='all':
                    all_res.append(pageNum)
            
    pdfFileObj.close()
    return all_res

def get_table_end(filename,start_page_num,check_page_n=1):
    pdfFileObj = open(filename,'rb')
    pdfReader = PyPDF2.PdfReader(pdfFileObj)
    all_res = []
    for pageNum in range(start_page_num+1,start_page_num+check_page_n+1):
            pageObj = pdfReader.pages[pageNum]
            content = pageObj.extract_text().lower().replace('\n','').replace('  ',' ')
            #pattern = re.compile(r'likelihood|policy response',re.I)
            pattern = re.compile(r'(?=.*likelihood)(?=.*policy response)(?=.*risk)')
            res = key_reg_match(content,reg_text = pattern,mode='rgx')
            if res:
                all_res.append(pageNum)
            else:
                if len(all_res)>0:
                    return all_res[-1]

## example of a matching function 
def matching_function(content):
    match_key = 'risk assessment matrix'
    if key_reg_match(content,search_text=match_key,mode='key'):
            pattern = re.compile(r'likelihood|policy response',re.I)
            # Search the text for the pattern
            res = key_reg_match(content,reg_text = pattern,mode='rgx')
            return res 
    return None

#%%
if __name__ == "__main__":
    file_path = "/root/workspace/data/DOCs/PDF/USA_2022.pdf"
    pgn = get_target_pagenum(file_path,matching_function,return_mode='first')
    end_pgn = get_table_end(file_path,pgn,check_page_n=2)
    print(pgn,end_pgn)

#%%




