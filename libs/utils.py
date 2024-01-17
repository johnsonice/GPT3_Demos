import json
import itertools
import pandas as pd
import pathlib,os,re
import logging 
import datetime 
from functools import wraps
import time

now = datetime.datetime.now()
name = os.getlogin()
USER = name.upper()
file_path = f"log/{USER}/{datetime.date.today()}"
os.makedirs(file_path,exist_ok=True)
filename = f"{file_path}/Exp-{now.hour}:{now.minute}.log"
fmt = "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"
logging.basicConfig(
    level=logging.INFO,
    filename=filename,
    filemode="w",
    format=fmt
    )



def load_json(f_path):
    with open(f_path) as f:
        data = json.load(f)
    
    return data

def load_jsonl(fn):
    result = []
    with open(fn, 'r') as f:
        for line in f:
            data = json.loads(line)
            result.append(data)
    return result 

def to_jsonl(fn,data,mode='w'):
    with open(fn, mode) as outfile:
        if isinstance(data,list):
            for entry in data:
                json.dump(entry, outfile)
                outfile.write('\n')
        else:
            json.dump(data, outfile)
            outfile.write('\n')

def flatten_list(list_of_lists):
    '''
    list_of_lists : TYPE
        any iregular list.
    Returns
    -------
    a flat list
    '''
    if len(list_of_lists) == 0:
        return list_of_lists
    if isinstance(list_of_lists[0], list):
        return flatten_list(list_of_lists[0]) + flatten_list(list_of_lists[1:])
    return list_of_lists[:1] + flatten_list(list_of_lists[1:])            

def hyper_param_permutation(hyper_params):
    ## prepare params for gride search ##
    assert isinstance(hyper_params,dict)
    param_names = list(hyper_params.keys())
    all_param_list = [hyper_params[k] for k in param_names]
    permu = list(itertools.product(*all_param_list))
    res = [dict(zip(param_names,i)) for i in permu]
    return res

def load_hp_res(hp_res_dir,to_csv_dir=None,sort_col=None):
    ## load hp tuning results 
    res = load_jsonl(hp_res_dir)
    df = pd.json_normalize(res,sep='_')
    
    if isinstance(sort_col, list):
        df.sort_values(by=sort_col,
                       ascending=False,
                       inplace=True)
    if isinstance(to_csv_dir,str):
        df.to_csv(to_csv_dir)
    
    return df,res

def get_best_hp_param(hp_res_dir:str,sort_col:list):
    ## get best param based on sorting criteria 
    df,hp_dict = load_hp_res(hp_res_dir,sort_col)
    best_param = hp_dict[df.index[0]]
    
    return best_param

def get_all_files(dirName,end_with=None): # end_with=".json"
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + get_all_files(fullPath)
        else:
            allFiles.append(fullPath)
    
    if end_with:
        end_with = end_with.lower()
        allFiles = [f for f in allFiles if pathlib.Path(f).suffix.lower() == end_with ] 

    return allFiles   

def exception_handler(error_msg='error handleing triggered',
                        error_return=None,
                        attempts=3,delay=1):
    '''
    follow: https://stackoverflow.com/questions/30904486/python-wrapper-function-taking-arguments-inside-decorator
    '''
    def outter_func(func):
        @wraps(func)
        def inner_function(*args, **kwargs):
            for i in range(attempts):
                try:
                    res = func(*args, **kwargs)
                    return res
                except Exception as e:
                    if i < attempts - 1:
                        print(f"Function failed with error {e}. Retrying after {delay} seconds...")
                        time.sleep(delay)
                    else:
                        custom_msg = kwargs.get('error_msg', None)
                        if custom_msg:
                            logging.error(custom_msg)
                        else:
                            logging.error(str(e))
                        res = error_return
                        return res 
        return inner_function
    
    return outter_func

def extract_json_string(text):
    """
    Extracts the string between ```json and ``` using regular expressions.
    Parameters:
    text (str): The text from which to extract the string.
    Returns:
    str: The extracted string, or an empty string if no match is found.
    """
    
    if not isinstance(text, str):
        raise ValueError("Input must be a string")
    
    # Regular expression to extract text between ```json and ```
    match = re.search(r'```json\s+(.*?)\s+```', text, re.DOTALL)

    # Return the extracted text if a match is found, otherwise return an empty string
    return match.group(1).strip() if match else ""


def parse_list_string(res_str):
    """
    Extracts numbered list items from a string.

    Each item is expected to start with a number followed by a parenthesis,
    e.g., "1) Item". Items are separated by new lines.

    Parameters:
    res_str (str): A string containing the numbered list items.

    Returns:
    list: A list of extracted items, with leading and trailing whitespace removed.
    """
    if not isinstance(res_str, str):
        raise ValueError("Input must be a string")
    # Compile the regular expression for efficiency if used multiple times
    pattern = r"\d+\)(.*?)(?=\n\d+\)|$)"
    # Find all matches and strip whitespace from each item
    items = [item.strip() for item in re.findall(pattern, res_str,re.DOTALL)]
    return items 


if __name__ == "__main__":
    
    
    inp_param = {'batch':[1,2,3],
                 'lr':[0.1,0.2,0.3]}
    
    res = hyper_param_permutation(inp_param)
    print(res)