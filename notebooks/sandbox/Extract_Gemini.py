# -*- coding: utf-8 -*-
"""
Created on Feb 11, 2025

@author: Kyun Chang with the help from ChatGPT and Gemini

"""
#%%
import pandas as pd
import numpy as np
import os
import time
import shutil
import re
import pathlib
from google import genai
from google.genai import types
import json
import sys
import datetime
sys.path.insert(1, 'Scripts')
from Utility_Doc_Management import get_files, combine_files,get_download_status,add_timestamp_to_filename
#%%
def process_pdfs(flist, path_pdf, path_ai, generation_config, PROMPT, clean_function):
    """Uploads PDFs one by one, runs the prompt, and saves responses."""

    for i, file in enumerate(flist):
        path = os.path.join(path_pdf, f'{file}.pdf')
        print(f" {i} Processing {file}...")

        try:
            print(f"Waiting {UPLOAD_DELAY} seconds before uploading...")
            time.sleep(UPLOAD_DELAY)
            
            myfile = client.files.upload(file=path)
            print(f"Uploaded")

            for attempt in range(1, RETRY_COUNT + 1):
                try:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        config=generation_config,
                        contents=[PROMPT, myfile],
                    )

                    if response.text:
                        print(response.text)
                        try:
                            response_data = json.loads(response.text)
                            df = pd.DataFrame(response_data)
                            df = clean_function(df)  # Use the provided cleaning function
                        except json.JSONDecodeError:
                            print("Response is not valid JSON. Saving raw text.")

                        # Save to CSV
                        if len(df) > 0:
                            df.to_csv(os.path.join(path_ai, f'{file}.csv'), index=False)
                            print(f"Extraction completed")
                            break  # Exit retry loop on success
                        else:
                            print(f"Empty response received.")
                    else:
                        raise ValueError("Empty response received.")
                
                except Exception as e:
                    print(f"Attempt {attempt} failed: {e}")
                    if attempt < RETRY_COUNT:
                        print(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                    else:
                        print(f"Failed to extract text after {RETRY_COUNT} attempts.")
        
        except Exception as e:
            print(f"Error processing: {e}")

    print("Extraction completed for all files.")


#%%
def combine_files(file_list, output_path=None):

    combined_data = []

    for file in file_list:
        try:
            # Determine the file type based on the extension
            file_extension = os.path.splitext(file)[-1].lower()

            if file_extension == '.csv':
                # Read the CSV file
                df = pd.read_csv(file)
            elif file_extension in ['.xls', '.xlsx']:
                # Read the Excel file
                df = pd.read_excel(file)
            else:
                print(f"Unsupported file type: {file}")
                continue

            # Add a column for the file name
            df['File Name'] = os.path.basename(file).split('.')[0]

            # Append the DataFrame to the list
            combined_data.append(df)
        except Exception as e:
            print(f"Error reading file {file}: {e}")

    # Combine all DataFrames into one
    combined_df = pd.concat(combined_data, ignore_index=True)

    # Save to a CSV file if output_path is provided
    if output_path:
        combined_df.to_csv(output_path, index=False)
        print(f"Combined DataFrame saved to {output_path}")

    return combined_df


#%%
def clean_REC(df):
    # Drop rows with all empty values
    df = df.dropna(how='all')
    df = df.dropna(subset=['Recommendation'],how='all')

    print(f"Number of unique file names after cleaning: {df['File Name'].nunique()}")
    return df

def clean_DAR(dar):

    cleaned_df = dar.copy()
    # Strip leading and trailing whitespace from 'Principle' and 'Assessment' columns
    cleaned_df['Principle'] = cleaned_df['Principle'].str.strip()
    cleaned_df['Assessment'] = cleaned_df['Assessment'].str.strip()

    # Remove rows with empty values in 'Principle' or 'Assessment' columns
    cleaned_df = cleaned_df.dropna(subset=['Principle', 'Assessment'])

    keyword_pattern = r'(compliance|rating|observance|principle|implement|compliant|observed|assessment|detailed|summary)'
    cleaned_df = cleaned_df[
        cleaned_df['Heading'].str.contains(keyword_pattern, flags=re.IGNORECASE, na=False).astype(int) +
        cleaned_df['Principle'].str.contains(keyword_pattern, flags=re.IGNORECASE, na=False).astype(int) +
        cleaned_df['Assessment'].str.contains(keyword_pattern, flags=re.IGNORECASE, na=False).astype(int) >= 2
    ]

    # Remove rows where 'Assessment' column has value 'X' or length > 100
    cleaned_df = cleaned_df[
        #(cleaned_df['Assessment'] != 'X') &
        (cleaned_df['Assessment'].str.len() <= 50)
    ]

    cleaned_df = cleaned_df[['Heading', 'Principle', 'Assessment', 'Theme']]

    print(f"Rows before cleaning: {len(dar)}")
    print(f"Rows after cleaning: {len(cleaned_df)}")

    return cleaned_df

def clean_RAM(ram):

    letter_pattern = r'[a-zA-Z]'
    keyword_pattern = r'(risk|assessment|matrix|ram)'
    likelihood_impact_keywords = ['high', 'medium', 'low', 'moderate', 'severe']

    # Remove rows where 'Likelihood' or 'Impact' columns contain no letters

    cleaned_df = ram[
        ram['Likelihood'].str.contains(letter_pattern, na=False) &
        ram['Impact'].str.contains(letter_pattern, na=False) &
        ram['Likelihood Full'].str.contains(letter_pattern, na=False) &
        ram['Impact Full'].str.contains(letter_pattern, na=False)
    ]

    # Remove rows where 'Heading' does not contain RAM keywords if 'Heading' is not missing
    cleaned_df = cleaned_df[
        cleaned_df['Heading'].isna() | 
        (cleaned_df['Heading'].str.count(keyword_pattern, flags=re.IGNORECASE) >=2)
    ]

    # Remove rows where 'Likelihood' or 'Impact' columns do not contain keywords from high, medium, low
    cleaned_df = cleaned_df[
        cleaned_df['Likelihood'].str.contains('|'.join(likelihood_impact_keywords), case=False, na=False) |
        cleaned_df['Impact'].str.contains('|'.join(likelihood_impact_keywords), case=False, na=False)
    ]

    # Keep only the specified columns
    cleaned_df = cleaned_df[['Heading', 'Risk', 'Likelihood', 'Likelihood Full', 'Impact', 'Impact Full']]

    print(f"Rows before cleaning: {len(ram)}")
    print(f"Rows after cleaning: {len(cleaned_df)}")

    return cleaned_df


#%%
def combine_extractions(list_of_dataframes):
    df= pd.concat(list_of_dataframes, ignore_index=True)
    df=df.drop_duplicates( keep='first')
    print(f"Number of unique rows after cleaning: {len(df)}")
    print(f"Number of unique file names after cleaning: {df['File Name'].nunique()}")
    return df

#%%
# Run the script
if __name__ == "__main__":

    # 1. Set up paths
    parent_path = r'U:\IFSAP 2025'
    path_pdf = os.path.join(parent_path, 'FSAP Documents\\External Vintages')
    path_word = os.path.join(parent_path, 'FSAP Documents\\External Vintages Converted')
    path_csv = os.path.join(parent_path, 'WIP')
    path_output = os.path.join(parent_path, 'Outputs')
    path_code = os.path.join(parent_path, 'Scripts')
    path_ai = os.path.join(parent_path, 'Gemini')
    
    # 2. Set up the API key and client
    # Configure the API key
    api_key = "xxx"
    client = genai.Client(api_key = api_key)

    # Delay settings (adjust as needed)
    UPLOAD_DELAY = 1  # Seconds to wait between uploads
    RETRY_COUNT = 2  # Maximum number of retries
    RETRY_DELAY = 5  # Seconds to wait between retries

    # GenAI configuration
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1048000,
    "response_mime_type": "application/json",
    }

    ##################################### extract recommendations ##################################

    # Define the prompt
    PROMPT_REC = (
    """
    Extract tables that meet the following condition:
    1. The tables should contain recommendations or recommended actions. 
    2. These tables have  "recommendation" or "recommendations" or "recommended actions" or "recommended action" in the text outside but before the table, or inside table as heading or as column name, but words such as not "updates" or "progress" shouldn't appear.        
    3. One document can have multiple tables like this. Make sure to include ALL of them 
    4. Some documents might not have this kind of tables. In that case, return nothing.

    The table identified and meet the conditions above should be extracted and put into a csv file with the following columns:  
    1. Heading (stores table name, table heading or table title, if not found, leave empty)
    2. Recommendation (stores the recommendation itself, can't be empty)
    3. Theme (appear with column names such as topic, theme, area, sector,subject OR appear as subheadings of the table. if not found, leave empty. For the recommendations belong to one theme, propagate the theme tag to all of them .)
    4. Timeframe (appear with column names such as time frame, timing, period,horizon, if not found, leave empty)
    5. priority (appear with column names such as priority, importance, urgency, if not found, leave empty)
    6. Authority (appear with column names such as authority, agency, entity, if not found, leave empty)
    7. Principle  (appear with column names such as principle, reference, responsibility, if not found, leave empty)

    Additionally, 
    1. If there are footnotes at the bottom of the table, remove it. 
    2. If the table is in mutiple pages, make sure to include all of them
    """
    )

    # 3. get the file list
    meta = pd.read_excel(os.path.join(path_output, 'Meta_File_List_External.xlsx'))
    folder_gemini=os.path.join(path_ai,'Run 0404 v1')
    meta = get_download_status(meta, folder_gemini, 'File Name')
    flist = meta[meta['Downloaded'] == 0]['File Name']
    file_path = [os.path.join(path_word, f'{f}.docx') for f in flist]
    print(f'The total documents that gonna process is {len(flist)}')

    attempt=3
    for i in range(0,attempt):
        process_pdfs(flist, path_pdf=path_pdf, path_ai=folder_gemini, generation_config=generation_config, PROMPT=PROMPT_REC)

        recomd_files = get_files(folder_gemini, 'csv')
        recomendations = combine_files(recomd_files, output_path=None )
        recomendations = clean_REC(recomendations)
        
        recomendation_updated = recomendation_updated.drop_duplicates()
        print(f"Number of unique recommendations after cleaning: {len(recomendation_updated)}")
        print(f"Number of unique file names after cleaning: {recomendation_updated['File Name'].nunique()}")
    
    recomendation_updated.to_excel(os.path.join(path_output, add_timestamp_to_filename('Recommendations.xlsx')), index=False)


    ################################## extract dar grades ##################################

    # Define the prompt
    PROMPT_DAR = (
    """
    Extract assessments from tables based on the following conditions:
        1. Identificatino of the right tables:
            1.1 Find the table that contains the principle by principle, detailed assessment for each principle: look for keywords such as "detailed assessment of ..." or "detailed compliance" or "detailed observance" in the title or heading outside but before the table, or inside table as heading or as column name
            1.2 Exclude tables containn words such as "progress", "action", "implementation" or implementation status" in title or heading.
            1.3 One document can have multiple principle by princple rating tables on different topics such as banking (BCP), insurance (IAIS) and securities (IOSCO). Make sure to include ALL of them.
        2. Identification of the right columns or rows:
            2.1 Identify the principle column: usually has "principle" or "recommendation"  as column name. For the content, it susually starts with keyword "principle" or "guideline" following by numbers or start with numbers. 
            2.2 Identify the assessment column: usually have "assessment" or "rating" or "grade" as column name. For the content in the column, the value can be abbreviations with only few letters or short phrase such as Fully Compliant, Largely Compliant or implemented, Partially Compliant or partially implemented, Non-Compliant or not implemented, Not fully implemented , partially implemented, not implemented, etc
        3. What if table can't be found with step 1 and 2:  
            3.1.ONLY look for tables with keywords such as "summary of compliance" or "summary of observance" or "rating summary" or "summary assessment" when can't find table by principle-by-principle rating.        
            3.2 Sometimes the table can cluster all principles with the same grade into one row, in that case, split the row into multiple rows, one for each principle.
        4. If still can't find any table, return nothing.


    The table identified and meet the conditions above should be extracted and put into a csv file with the following columns:  
        1. Heading (stores table name, table heading or table title, if not found, leave empty)
        2. Principle (stores principle or guideline, usually have keyword principle or guideline or similar words or principle number, can't be empty)
        3. Assessment (stores the grade or assessment or rating , can't be empty, usually the column name can be assessment or rating or grade or word with similar meanings. The value can be abbreviations with only few letters or short phrase such as"Fully Compliant", "Largely Compliant" or "implemented", "Partially Compliant" or "partially implemented", "Non-Compliant" or "Implemented","not implemented", "Not fully implemented" , "partially implemented", etc)
        4. Theme (a categorical column has four possible values: BCP if the table related to bank regulation/basel, IAIS if the table related to insurance regulation, IOSCO if the table related to securities regulation. Others if can't identify the previous three categories. For the recommendations belong to one theme, propagate the theme tag to all of them .) 
        
    
    Additionally, keep in mind the important details in the handling process, 
    1. If there are footnotes at the bottom of the table, remove it. 
    2. If the table is in mutiple pages, make sure to include all of them
    """
    )
    # Process the PDFs

    meta = pd.read_excel(os.path.join(path_output, 'Meta_File_List_External.xlsx'))
    folder_gemini=os.path.join(path_ai,'Run 0417 v1 DAR')
    meta = get_download_status(meta, folder_gemini, 'File Name')
    meta=meta[meta['DAR']==1]
    len(meta)
    flist = meta[meta['Downloaded'] == 0]['File Name']
    file_path = [os.path.join(path_word, f'{f}.docx') for f in flist]
    print(f'The total documents that gonna process is {len(flist)}')


    attempt=3
    for i in range(0,attempt):
        process_pdfs(flist, path_pdf=path_pdf, path_ai=folder_gemini, generation_config=generation_config,PROMPT=PROMPT_DAR,clean_function=clean_DAR)
        
        dar_files = get_files(folder_gemini, 'csv')
        dar = combine_files(dar_files, output_path=None )
        dar_updated = dar.drop_duplicates()
        print(f"Number of unique recommendations after cleaning: {len(dar_updated)}")
        print(f"Number of unique file names after cleaning: {dar_updated['File Name'].nunique()}")

        flist=[f for f in flist if f not in dar['File Name'].unique()] 

    dar.to_excel(os.path.join(path_output, add_timestamp_to_filename('DAR.xlsx')), index=False)
    dar=pd.read_excel(os.path.join(path_output, 'DAR_20250417.xlsx'))

    #########################extract risk assessment matrix##########################
    PROMPT_RAM = (
    """
    Extract risk assessment matric from tables based on the following conditions:
        Identificatino of the correct tables:
            1. Look for keywords such as "RAM" or "risk assessment matrix" or "Risk Assessment Matrix" or "overall level of concern" in the title or heading before the table, or inside table as heading or as column name. 
            2. The table can be long and split into multiple pages, make sure to include all of them.
            4. The table could appear at the very bottom of the document, try to look for the appendix section and table with column names such as "source"/"risk", "likelihood" or "impact" if can't find the table in the main body of the document. 
            3. If still can't find the table, return nothing.


        The table identified and meet the conditions above should be extracted and put into a csv file with the following columns:  
            1. Heading (stores table name, table heading or table title, if not found, leave empty)
            2. Risk (stores risk, usually has keyword "risk" or "threat" or "source" in column name and contain long descriptive writing, can't be empty)
            3. Likelihood Full(stores likelihood of risk realization, usually has keyword "likelihood" in column name. The text may include multiple paragraphs as bullet points with large blank spaces between, extract EVERYTHING in the column, can't be empty)
            4. Likelihood (fpr the same column above, extract the value from the first line which describes the level of likelyhood with words such as "high" "medium" "low")
            5. Impact Full (stores the impact of realization/materialization of the risk, usually has keyword "impact" in column name. The text may include multiple paragraphs as bullet points with large blank spaces between, extract EVERYTHING in the column, can't be empty)
            6. Impact (for the same column above, extract the value from the first line which describes the level of impact with words such as "high" "medium" "low") 
            
        Additionally, keep in mind the important details in the handling process, 
        1. If there are footnotes at the bottom of the table, remove it. 
        """
)

    meta = pd.read_excel(os.path.join(path_output, 'Meta_File_List_External.xlsx'))
    folder_gemini=os.path.join(path_ai,'Run 0416 v1 RAM')
    meta = get_download_status(meta, folder_gemini, 'File Name')
    meta=meta[meta['Doc Type'].isin(['FSSA'])]
    flist = meta[meta['Downloaded'] == 0]['File Name']
    print(f'The total documents that gonna process is {len(flist)}')
    

    attempt=3
    for i in range(0,attempt):

        process_pdfs(flist, path_pdf=path_pdf, path_ai=folder_gemini, generation_config=generation_config,PROMPT=PROMPT_RAM,clean_function=clean_RAM)

        # 2. List files in the directory
        ram_files = get_files(folder_gemini, 'csv')
        ram = combine_files(ram_files, output_path=None )
        ram_updated = ram.drop_duplicates()
        print(f"Number of unique recommendations after cleaning: {len(ram_updated)}")
        print(f"Number of unique file names after cleaning: {ram_updated['File Name'].nunique()}")

        flist=[f for f in flist if f not in ram_updated['File Name'].unique()]
   
    # Save the cleaned DataFrame to a xlsx file
    ram_updated.to_excel(os.path.join(path_output, add_timestamp_to_filename('RAM.xlsx')), index=False)

