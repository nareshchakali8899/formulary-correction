import sys, pickle
import pandas as pd

sys.path.append('/home/dileep/github_repos/formulary_correction')

from helpers import open_file

def generate_component_pkl(components):

    comp_df = pd.json_normalize(components)
    component_dict = comp_df[['name', '_id.$oid']].to_dict(orient='dict')

    new_dict = {}

    for idx,name in component_dict.get('name').items():

        mongo_id = component_dict.get('_id.$oid').get(idx)
        new_dict[name] = int(mongo_id, 16)

    with open('./data/component_idx.pkl', 'wb') as file:
        pickle.dump(new_dict, file)
        
    print('Created component_idx.pkl!!!')

def generate_std_med_ls(orderables):

    standardized_med_dict = {}

    for idx, orderable in enumerate(orderables):

        components = orderable.get('components')
        name = orderable.get('name')

        if components:

            standardized_med_name = ','.join(sorted([str(int(component.get('$oid'), 16)) for component in components]))
            smn_dict = {}
            smn_dict['index'] = idx
            smn_dict['name'] = name
            standardized_med_dict[standardized_med_name] = smn_dict


    with open('./data/standardized_med_names.pkl', 'wb') as file:
        pickle.dump(standardized_med_dict, file)
        
    print('Created standardized_med_names.pkl!!!')

def generate_link_df():

    # Creating component_df
    component_df = pd.DataFrame.from_dict(open_file('orderables/component_idx.pkl', 'pkl'), orient='index').reset_index().rename(columns={'index':'component', 0:'cp_id'})
    component_df['cp_id'] = component_df['cp_id'].astype(str)

    # Creating orderable component mongo collection link df
    ord_dict = open_file('./data/standardized_med_names.pkl', 'pkl')
    ord_dict = {v.get('index'): ([v.get('name')] + k.split(',')) for k,v in ord_dict.items()}
    ord_df = pd.DataFrame.from_dict(ord_dict, orient='index').reset_index().rename(columns={'index':'mongo_index'})
    ord_df = ord_df.melt(id_vars=['mongo_index', 0]).drop('variable', axis=1).dropna(subset=['value']).reset_index(drop=True).rename(columns={'value':'cp_id',
                                                                                                                                             0:'name'})
    ord_df['cp_id'] = ord_df['cp_id'].astype(str)
    
    print('Created link df!!!')
    
    return ord_df

standardized_med_dict = open_file('./data/standardized_med_names.pkl', 'pkl')

def lookup_item(item_name, link_df, look_up_col='name'):
    '''
    look_up_col - str, can be name, mongo_index or smn
    '''
    if look_up_col!='smn':
        sample_df = link_df[link_df[look_up_col]==item_name]
        smn = ','.join([str(y) for y in sorted([int(x) for x in list(sample_df['cp_id'])])])
    else:
        smn = item_name

    return (smn, standardized_med_dict.get(smn))

# generate_component_pkl(components)
# generate_std_med_ls(orderables)
# generate_link_df()
