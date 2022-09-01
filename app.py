from logging import warning
from time import sleep
import streamlit as st
from helpers import get_med_name
import json
from clean_orderables import update_correction , update_string_with_replacement, update_with_link_dict
from tqdm import tqdm
from helpers import get_match_string, get_suggested_name,load_run_files
from fuzzywuzzy import process, fuzz
import streamlit.components.v1 as components



with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>',unsafe_allow_html=True)

st.title("Formulary Correction")

if 'count' not in st.session_state:
    st.session_state['count'] = 0


def display_options(match_item, match_str, match, suggested_name):

    correct_obj = {}
    incorrection_obj = {}
    warning_msg = st.empty()

    correction_form = st.empty()

    my_form = correction_form.form(clear_on_submit=True, key=f'myform_{st.session_state.count}')

    with my_form:
        html = f"""<div >
        <p style="font-weight:bold">ITEM:<span style="color:red"> {str(match_item)}</span></p>
        </div>"""
        components.html(html, height=40)
        col_1,col_2 = st.columns(2)
        col_1.markdown('<p class="form_title">Select Correct Item</p>',unsafe_allow_html=True)
        if match < 100:
            col_1.write(f'SUGGESTED NAME: {suggested_name}')
        for item in range(len(match_str)):
            correct_obj[item+1] = col_1.checkbox(match_str[item], value=False,key=f'correctiion_{st.session_state.count}_{item}')
        replace_txt = col_1.text_input("Other :")

        col_2.markdown('<p class="form_title">Select Incorrect Items</p>',unsafe_allow_html=True)
        for item in range(len(match_str)):
            incorrection_obj[item+1] = col_2.checkbox(match_str[item], value=False,key=f'incorrectiion_{st.session_state.count}_{item}')

    cols = my_form.columns(5)
    submitted = cols[0].form_submit_button("Correct")
    no_correction = cols[1].form_submit_button("No Correction")
    link = cols[2].form_submit_button("Link")

    correct_data = []
    incorrect_data = []
    btn_type = ""

    for key in incorrection_obj:
        if incorrection_obj[key]:
            incorrect_data.append(key)

    for key in correct_obj:
        if correct_obj[key]:
            correct_data.append(key)
    
    if submitted:
        if replace_txt:
            if len(incorrect_data)>0:
                warning_msg.empty()
                btn_type = "replace"
                correction_form.empty()  
            else:
                warning_msg.warning("Please Select atleast one item from right side box.")

        else:
            if len(correct_data)==1:                   
                if len(incorrect_data)>0:
                    btn_type = "correction"
                    correction_form.empty()  
                else:
                    warning_msg.warning("Please Select atleast one item from right side box")
            else:
                warning_msg.warning("Please Select any one correct item from left side box")
    if no_correction:
        correction_form.empty()
        btn_type = "no_correction"

    if link:
            if len(correct_data)==1:                   
                if len(incorrect_data)>0:
                    btn_type = "link"
                    correction_form.empty()  
                else:
                    warning_msg.warning("Please Select atleast one item from right side box")
            else:
                warning_msg.warning("Please Select any one correct item from left side box")

    return correct_data,incorrect_data, btn_type ,replace_txt


def suggestedName(match_item, google_suggestion=False):
    # Doing a google search and getting suggestions
    suggested_name = ""
    if google_suggestion:

        try:
            suggested_name = get_suggested_name(match_item)
            match = fuzz.ratio(match_item.lower(), suggested_name.lower())
        except:
            # print(f'{bcolors.BOLD}{bcolors.FAIL}\nCOULD NOT GET SUGGESTED NAME\n{bcolors.ENDC}')
            st.warning("COULD NOT GET SUGGESTED NAME")
            match = 100
    else:

        match = 100

    return suggested_name, match


def submit_correction(medicine_names):
    suggested_name, match = suggestedName(
        medicine_names[st.session_state.count])
    match_str, ls = get_match_string(
        medicine_names[st.session_state.count], medicine_names, threshold=90, limit=10)
    correct_item, correction_data, btn_type, correction_str = display_options(medicine_names[st.session_state.count], match_str, match, suggested_name)
    if len(correction_data) > 0 or btn_type == 'no_correction':
        success_dialog = st.empty()
        if btn_type == 'correction':
            update_correction(
                0, ls,st.session_state.count, ls[correct_item[0]],correction_data)
            st.session_state.count += 1
            success_dialog.success("Successfully Submited")
            sleep(1)
            success_dialog.empty()
            submit_correction(medicine_names)
            load_run_files(st.session_state.count-1)
        elif btn_type == 'link':
            update_with_link_dict(0, medicine_names, st.session_state.count,ls[correct_item[0]],correction_data)
            st.session_state.count += 1
            success_dialog.success("Successfully Submited")
            sleep(1)
            success_dialog.empty()
            submit_correction(medicine_names)
            load_run_files(st.session_state.count-1)
        elif btn_type == "replace":
            update_string_with_replacement(0, ls, st.session_state.count, correction_str,correction_data)
            st.session_state.count += 1
            success_dialog.success("Successfully Submited")
            sleep(1)
            success_dialog.empty()
            submit_correction(medicine_names)
            load_run_files(st.session_state.count-1)
        else:
            st.session_state.count += 1
            submit_correction(medicine_names)

st.write("Progress :")
progress = st.progress(st.session_state.count)

file_data = st.file_uploader("Upload File", type=['json'])

if file_data is not None:
    json_file = json.load(file_data)
    medicine_names = get_med_name(json_file)
    medicine_names = sorted(medicine_names)
    submit_correction(medicine_names)

