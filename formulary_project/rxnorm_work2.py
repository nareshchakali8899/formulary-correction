
import boto3, requests
from collections import defaultdict

comprehend_med = boto3.client('comprehendmedical', region_name='ap-southeast-2')

def get_drug_dictionary(name, only_comprehend=False):
    """Main function that takes in drug name and returns a dictionary 
    with the RxNormId and component details
    
    name: string, name of drug
    """

    if only_comprehend:
        
        detects = comprehend_med.infer_rx_norm(Text=name).get('Entities')
        drug_dict = get_probable_codes(detects, 0.9)
        
    else:
    
        rx_url = f'https://rxnav.nlm.nih.gov/REST/rxcui.json?name={name}&search=1'
        codes = requests.get(rx_url).json().get('idGroup').get('rxnormId')
        drug_dict = {name:codes}

        if (codes==None):
            detects = comprehend_med.infer_rx_norm(Text=name).get('Entities')
            drug_dict = get_probable_codes(detects, 0.9)
        
    drug_details = []; component_names = []
    if drug_dict:
        for component_name, codes in drug_dict.items():
            component_names.append(component_name.title())
            
            for code in codes:
            
                rx_class_callback = call_rx_class_api(code)
                drug_details.extend(get_drug_details(rx_class_callback, code))

    drug_dict = {
        'drug_name':name,
        'component_details':drug_details
    }
    
    return drug_dict

def get_probable_codes(detects, threshold):
    '''From the list of comprehend_med detects, extracts the rx_norm codes that
    haver >threshold probability
    
    detects: list, List of entities detected from comprehend medical
    threshold: float, Threshold above which the code should be added to output
    '''

    drug_dict = defaultdict(list)
    for detect in detects:
        
        rx_concepts = detect.get('RxNormConcepts')
        text = detect.get('Text')

        for concept in rx_concepts:

            pred_proba = concept.get('Score')
            code = concept.get('Code')

            if pred_proba>0.9:
                drug_dict[text].append(code)
                
    return drug_dict

def call_rx_class_api(code):
    """Function that makes API calls to RxNorm to get drug details
    code: string or int, RxCUI 
    """

    rx_url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui={code}&relaSource=ATC"
    #rx_url = "https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui=82122&relaSource=FMTSME&relas=has_tc"

    r = requests.get(rx_url)

    return r.json()

def get_drug_details(rx_class_callback, code):
    """Cleans the API call back in the form of a dictionary
    rx_class_callback: dict, call back from RxAPI
    """
    
    # Unnesting
    dil = rx_class_callback.get('rxclassDrugInfoList')
    if dil:
        drug_info_list = dil.get('rxclassDrugInfo')
    else:
        return {}

    drug_details = {}; graph_set = set()
    # Getting drug details
    for info_item in drug_info_list:
        
        component_dict = defaultdict(set)
        class_name, class_id, drug_name = get_item_details(info_item)
        
        if code in drug_details.keys():
            
            component_dict = drug_details.get(code)
            
            component_dict['rx_norm'].add(code)
            component_dict['atc_class_name'].add(class_name)
            component_dict['atc_class'].add(class_id)
            graph_set = graph_set.union(get_class_graph(class_id))
            
            if graph_set:
                component_dict['atc_graph'] = graph_set
            
        else:
            
            component_dict['rx_norm'].add(code)
            component_dict['atc_class_name'].add(class_name)
            component_dict['atc_class'].add(class_id)
            component_dict['atc_graph'] = set()
            graph_set = graph_set.union(get_class_graph(class_id))
            
            if graph_set:
                component_dict['atc_graph'] = graph_set
            
            drug_details[code] = component_dict
#             drug_details.append({'rx_norm':code, 'component_name':drug_name, 'atc_class_name':class_name, 
#                                  'atc_class':class_id})

    return unnest(drug_details)

def get_item_details(info_item):
    """Function to rearrange rx_api_callback to specified format
    info_item: dict
    """

    # Getting class_name
    class_info = info_item.get('rxclassMinConceptItem')
    if class_info:
        class_name = class_info.get('className')
        class_id = class_info.get('classId')

    # Getting drug_name
    drug_info = info_item.get('minConcept')
    if drug_info:
        drug_name = drug_info.get('name')

    return class_name, class_id, drug_name

def get_class_graph(class_id):
    '''This gives the ATC class graph heirarchy of a particular class code'''
    url = f'https://rxnav.nlm.nih.gov/REST/rxclass/classGraph.json?classId={class_id}'
    call_back = requests.get(url).json().get('rxclassGraph')
    if call_back:
        graph = call_back.get('rxclassMinConceptItem')
        class_ids = set()
        for g in graph:
            class_ids.add(g.get('classId'))
        
        return class_ids

    
def unnest(ddict):

    item_ls = [dict(x) for x in list(ddict.values())]
    unnest_items = ['rx_norm']
    
    new_ls = []
    for item in item_ls:
        
        unnested_dict = {}
        for k,v in item.items():
            if k in unnest_items:
                unnested_dict[k] = list(v)[0]  
            else:
                unnested_dict[k] = list(v)
        
        new_ls.append(unnested_dict)
            
    return new_ls


# drug_json_list = []

# for i in range(len(med_items)):
#     if i<1347:
#         continue
#     name = med_items.loc[i, 'name']
#     print(i, name)
#     if name:
#         drug_json_list.append(get_drug_dictionary(name))

# components = []

# for file in json_file:
    
#     drug_name = file.get('drug_name')
#     rx_norm_ids = file.get('rx_norm_ids')
#     component_details = file.get('component_details')
    
#     if component_details:
        
#         for component in component_details:
#             component['drug_name'] = drug_name
#             component['rx_norm_ids'] = rx_norm_ids
            
#             components.append(component)    
