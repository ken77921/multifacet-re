import sys
import os
import codecs
from collections import defaultdict
import xml.etree.ElementTree as ET
import copy

def load_hop2_query(hop2_query_expanded_path):
    hop2_queryID2hop1_sf={}
    tree = ET.parse(hop2_query_expanded_path)
    root = tree.getroot()
    for child in root.findall('query'):
        hop2_queryID=child.attrib['id']
        hop1_sf=child[0].text
        hop2_queryID2hop1_sf[hop2_queryID]=hop1_sf

    return hop2_queryID2hop1_sf


def hop2_queryID2hop1_queryID(hop2_queryID):
    hop1_end_index=hop2_queryID.rfind('_')
    hop1_queryID=hop2_queryID[:hop1_end_index]
    return hop1_queryID


def filter_candidates_and_output(scored_candidates_path,hop2_queryID2hop1_sf,hop1_query_sf2conf_rel,inv_rel_mapping,hop1_rel2current_thresh,output_path):
    f_out=open(output_path,"w")
    with open(scored_candidates_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            #CSSF15_ENG_eda98a9e8a_ec8c5bad40a1      org:alternate_names     International Pentecostal Church        f803cee34a844bc34bb87e4d590e6243:CSSF15_ENG_eda98a9e8a_ec8c5bad40a1:34:4118-4149:4144-4159:4072-4212    10      13      17      20      0.96467082468492
            fields=line.split('\t')
            if( len(fields)<8 ):
                #f_out.write(line+'\n')
                continue
            #hop2_queryID,rel,teamID,provenance,slot_filler,filler_type,sf_prov,conf_score=fields
            hop2_queryID,rel,teamID,provenance,slot_filler,ent1_start,ent1_end,ent2_start,ent2_end,conf_score=line.split("\t")
            hop1_queryID=hop2_queryID2hop1_queryID(hop2_queryID)
            hop1_sf=hop2_queryID2hop1_sf[hop2_queryID]
            hop1_query_sf=hop1_queryID+'|'+hop1_sf
            if( hop1_query_sf not in hop1_query_sf2conf_rel):
                print "Ingoring ",hop1_query_sf, ", because the mismatch between hop1 response and hop2 query file. The reason might be some special character problem"
                continue
            hop1_conf,hop1_rel=hop1_query_sf2conf_rel[hop1_query_sf]
            if(hop1_rel in inv_rel_mapping):
                #print hop1_rel
                hop1_rel=inv_rel_mapping[hop1_rel][0]
            #print hop1_conf, hop1_rel2current_thresh[hop1_rel]
            if(hop1_conf < hop1_rel2current_thresh[hop1_rel]):
                continue
            f_out.write(line+'\n')
    
    f_out.close()

def load_hop1_response(hop1_response_path):
    hop1_query_sf2conf_rel={}

    with open(hop1_response_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            #print line
            queryID,rel,teamID,provenance,slot_filler,filler_type,sf_prov,conf_score=line.split("\t")
            
            hop1_query_sf2conf_rel[queryID+'|'+slot_filler]=[float(conf_score),rel]

    return hop1_query_sf2conf_rel

def load_inv_mapping(rel_not_handled_path,inverse_mapping_path):
    rel_not_handled_set=set()
    with open(rel_not_handled_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","").strip()
            if( len(line) == 0):
                continue
            rel_not_handled_set.add(line)

    inv_rel_mapping={}
    with open(inverse_mapping_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            rel,inv_rels_str=line.split('\t',1)
            if(rel not in rel_not_handled_set):
                continue
            inv_rel_mapping[rel]=inv_rels_str.split('\t')

    return inv_rel_mapping

def load_threshold(initial_params_path):
    hop1_rel2current_thresh={}
    with open(initial_params_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            rel,thresh=line.split(' ')
            hop1_rel2current_thresh[rel]=float(thresh)
    return hop1_rel2current_thresh

if __name__ == '__main__':
    scored_candidates_path=sys.argv[1] 
    hop2_query_path=sys.argv[2]
    hop1_responses_path=sys.argv[3]
    
    rel_not_handled_path=sys.argv[4]
    inverse_mapping_path=sys.argv[5]

    hop1_tuned_params_path=sys.argv[6]
    output_path=sys.argv[7]

    inv_rel_mapping=load_inv_mapping(rel_not_handled_path,inverse_mapping_path)
    hop2_queryID2hop1_sf=load_hop2_query(hop2_query_path)
    hop1_query_sf2conf_rel=load_hop1_response(hop1_responses_path)
    hop1_rel2current_thresh=load_threshold(hop1_tuned_params_path)

    filter_candidates_and_output(scored_candidates_path,hop2_queryID2hop1_sf,hop1_query_sf2conf_rel,inv_rel_mapping,hop1_rel2current_thresh,output_path)
