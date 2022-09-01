
import os, json, pickle, nest_asyncio, re
from time import sleep
from collections import defaultdict
from fuzzywuzzy import process
from search_engine_parser import GoogleSearch
import wikipedia
import streamlit as st

def google(query):
    search_args = (query, 1)
    gsearch = GoogleSearch()
    gresults = gsearch.search(*search_args)
    return gresults['links']

# nest_asyncio.apply()

def find_closest_match_from_google(drug_name):

    search_results = google(drug_name)

    clean_text = lambda x: x.replace('https://', '').replace('www.', '').replace('.html', '')

    bow = []
    for one_result in search_results:

        one_result = clean_text(one_result)
        bow.extend(re.split(r'\.|\/|\-', one_result))

    closest_matches = process.extract(drug_name, bow)
    closest_matches = [match for match in closest_matches if match[-1]>=90]

    if closest_matches:
        closest_match = closest_matches[-1][0]
    else:
        closest_match = ''
    
    return closest_match.title()

def get_suggested_name(query):

    queries = re.split('\s', query)
    suggested_name = ' '.join([find_closest_match_from_google(q) for q in queries])

    return suggested_name.strip()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def write_as_pkl(source, destination):

    with open(destination, 'wb') as file:
        pickle.dump(source, file)
        
    print(f"Stored file as {destination}")

def open_file(path, file_type='json'):
    """
    Script to open json and pickle files quickly
    path: str, path to file
    file_type: str, either json or pkl
    """
    
    if file_type=='json':
        with open(path) as file:
            json_file = json.load(file)

        return json_file
    
    elif file_type=='pkl':
        with open(path, 'rb') as file:
            pkl_file = pickle.load(file)
            
        return pkl_file
    
    else:
        print('Type unknown..')
        return None

def update_correction_dict(match_item, correction, correction_dict, ls, del_ls):

    if correction>0:
        correct = match_item
        to_correct = ls[correction]
    elif correction<0:
        to_correct = ls[abs(correction)]
        correct = match_item
        
        del_ls.append(ls[ls.index(to_correct)])
    
    
    update_dict_with_logs(correct, [to_correct], correction_dict, 'correction')
    
    return correction_dict, del_ls

def load_run_files(from_backup):
    if from_backup:
        correction_dict = open_file(f'data/backup/{from_backup}/corrections.pkl', 'pkl')
        del_ls = open_file(f'data/backup/{from_backup}/del_ls.pkl', 'pkl')
        link_dict = open_file(f'data/backup/{from_backup}/link_dict.pkl', 'pkl')
            
    else:
        correction_dict = defaultdict(list)
        link_dict = defaultdict(list)
        del_ls = []
        correction_dict['correct'].append('to be corrected')
        
    return correction_dict, link_dict, del_ls

def get_match_string(match_item, component_ls, threshold=90, limit=10):
    
    match_ls = process.extract(match_item, component_ls, limit=limit)

    ls = []; new_ls = []; count = 1
    ls.append("None")

    for item_name, match_score in match_ls:
        if match_score>=threshold:

            ls.append(item_name)

            if match_score<100:
                new_ls.append(f"{item_name}")
            else:
                new_ls.append(f"{item_name}")

            count+=1

    # match_str = new_ls
    
    return new_ls, ls

def update_link_dict(correct_item,index_choices, ls, link_dict):

    key_med = correct_item
    val_meds = [ls[int(v)] for v in index_choices]
    
    update_dict_with_logs(key_med, val_meds, link_dict, 'link')

    return link_dict

def update_with_replacement(index_choices,correction, correction_dict, ls, del_ls):
    
    val_meds = [ls[int(v)] for v in index_choices]
    
    update_dict_with_logs(correction, val_meds, correction_dict, 'correction')
    del_ls.extend(val_meds)
    
    return correction_dict, del_ls

def update_dict_with_logs(key, val, dic, update_type):
    
    print(f'\n{bcolors.BOLD}Correct: {key} To correct: {val}{bcolors.ENDC} in {update_type} dictionary'.upper())
    dic[key].extend(val)
    
    print('_'*30)

def backup_files(correction_dict, link_dict, del_ls, idx):
    
    try:
        os.mkdir(f'data/backup/{idx}')
    except FileExistsError:
        pass
    
    write_as_pkl(correction_dict, f'data/backup/{idx}/corrections.pkl')
    write_as_pkl(del_ls, f'data/backup/{idx}/del_ls.pkl')
    write_as_pkl(link_dict, f'data/backup/{idx}/link_dict.pkl')
    
    print('Backed up files..')
    
def explain_code(code):
    
    code = code[0]
    print(code)
    search_string = f"ATC code {code}"
    pattern_string = f"(?<={search_string})(.*)(?=is a)"
    pattern = re.compile(pattern_string)
    
    print(search_string)
    wiki_content = wikipedia.page(search_string).content

    return re.search(pattern, wiki_content).group().strip()


def get_med_name(data):
    med_name = []
    for med in data:
        med_name.append(med["name"])
    
    return med_name

