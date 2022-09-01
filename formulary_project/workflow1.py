
import pandas as pd
from .rxnorm_work2 import get_drug_dictionary
import re
import json
from tqdm import tqdm

def split_delim(strings, delims):
    
    pattern = re.compile('\\' + '|\\'.join(delims))
    
    break_ls = []
    for string in strings:
        
        break_ls.extend(re.split(pattern, string))
        
    break_ls = [name.strip().title() for name in break_ls]
            
    return break_ls

def remove_dict_duplicates(dict_list):

    seen = set()
    new_l = []
    for d in dict_list:
        t = str(d)
        if t not in seen:
            seen.add(t)
            new_l.append(d)
            
    return new_l

class Orderables:
    '''
    df - Has to have one column called "generic", one named "brand"
    '''

    def __init__(self, df, delims):
        self.df = df
        self.json = df.to_json(orient='records')
        self.drug_list = df.generic.unique()
        self.orderables_list = []
        self.delims = delims
        self.component_idx = open_file('orderables/component_idx.pkl', 'pkl')
        self.smn = open_file('orderables/standardized_med_names.pkl', 'pkl')
        self.current_orderables = open_file('/home/ec2-user/SageMaker/data-pipeline/data/jsons/orderables.json')
        self.added_components = set()

    def orderable_json(self, only_comprehend=False):
        
        print(f"{len(self.drug_list)} unique items..")
        delims = self.delims
#         comprehend_callbacks = self.comprehend_callbacks
        
        # Iterating through generic names
        count = 0
        for drug_name in tqdm(self.drug_list):
            count = count + 1
            orderable = {}
            
            # Here df is being subset to have just the name of the generic
            drug_df = self.df.loc[self.df['generic'] == drug_name]
            orderable['type'] = 'med'
            orderable['class'] = ''
            orderable['name'] = '/'.join([n.title() for n in split_delim([drug_name], delims)])

            # For adding components
            orderable['components'] = []
            
            # SPLITTING DRUG NAME USING DELIMITER
            drug_names = split_delim([drug_name], delims)
            drug_names = [name for name in drug_names if name!='']
            
            # ITERATING INDIVIDUAL COMPONENT NAME
            for name in drug_names:
                
                # IF COMPONENT IS KNOWN TO US
                if name in self.component_idx.keys():
                    
                    # ADD COMPONENT TO THE COMPONENTS SECTION OF OUR ORDERABLE ITEM
                    orderable['components'].append({'$oid':hex(self.component_idx.get(name)).replace('0x', '')})
                
                # IF COMPONENT IS NOT KNOWN TO US
                else:
                    
                    # FIND THE COMPONENT DETAILS USING COMPREHEND MEDICAL 
                    comp_dict = get_drug_dictionary(name, only_comprehend=only_comprehend)
                    component_details = comp_dict.get('component_details')
                    
                    # ADD COMPONENT AS A REGULAR DICT (NOT AS A RELATION - THIS HAS TO BE DONE BY BACKEND)
                    # AND AFTER BACKEND HAS DONE THIS, COMPONENT PKL HAS TO BE UPDATED
                    component = {}
                    if component_details:
                        for component_detail in component_details:
                            
                            component = component_detail
                            component['component_name'] = name.title()
                            component['snomed'] = {'code':None, 'name':None}
                            orderable['components'].append(component)
                            self.added_components.add(name.title())
                            
                    else:
                        component['component_name'] = name.title()
                        component['snomed'] = {'code':None, 'name':None}
                        orderable['components'].append(component)
                        self.added_components.add(name.title())
                    
                try:
                    # For adding presets
                    components = orderable.get('components')
                    sm_name = ','.join(sorted([str(int(component.get('$oid'), 16)) for component in components]))
                    if sm_name in self.smn.keys():
                        orderable['presets'] = self.current_orderables[self.smn.get(sm_name).get('index')].get('presets')
                except TypeError:
                    orderable['presets'] = []

                # For adding Brands
                brands = []
                for idx,row in drug_df.iterrows():
                    brands.append(row['brand'])
                    orderable['brands'] = brands

                self.orderables_list.append(orderable)
        
        self.orderables_list = remove_dict_duplicates(self.orderables_list)
        print(f"{len(self.orderables_list)} orderables has to be added to the orderables collection..")
        print(f"{len(self.added_components)} components has to be added to the components collection..")
            
#             with open('orderables/comprehend_callbacks.json', 'w') as file:
#                 json.dump(comprehend_callbacks, file)

        return self.orderables_list 
