
import os
import threading
from fuzzywuzzy import process, fuzz
from IPython.display import clear_output
from tqdm import tqdm
from collections import defaultdict

from helpers import  *
import streamlit as st

try:
    os.makedirs('data/backup/')
except:
    pass


def update_correction(from_backup, ls, idx, correct_item,correction):
    correction_dict, link_dict, del_ls = load_run_files(from_backup)
    for corret in correction:
        correction_dict, del_ls = update_correction_dict(
            correct_item, corret, correction_dict, ls, del_ls)
    if idx % 10 == 0:
        backup_files(correction_dict, link_dict, del_ls, idx)
    backup_files(correction_dict, link_dict, del_ls, idx)


def update_with_link_dict(from_backup, ls, idx,correct_item,index_choices):
    correction_dict, link_dict, del_ls = load_run_files(from_backup)
    link_dict = update_link_dict(correct_item,index_choices,ls, link_dict)
    if idx % 10 == 0:
        backup_files(correction_dict, link_dict, del_ls, idx)
    backup_files(correction_dict, link_dict, del_ls, idx)


def update_string_with_replacement(from_backup, ls, idx,correction,index_choices):
    correction_dict, link_dict, del_ls = load_run_files(from_backup)
    correction_dict, del_ls = update_with_replacement(index_choices,correction, correction_dict, ls, del_ls)
    if idx % 10 == 0:
        backup_files(correction_dict, link_dict, del_ls, idx)
    backup_files(correction_dict, link_dict, del_ls, idx)