import sys
import os
import codecs
import unicodedata
from collections import defaultdict
import xml.etree.ElementTree as ET
import copy

CORRECT=1
WRONG=0
CONTRADICT=-1
UNASSESSED=-2
PARENT_WRONG=-3
DUPLICATION=-4

def update_cw(correct_for_response,total_cw):
    if(correct_for_response == CORRECT):
        total_cw[1]+=1
    if(correct_for_response == WRONG or correct_for_response == PARENT_WRONG or correct_for_response == DUPLICATION):
        total_cw[0]+=1

def single_hop_pooling(fixed_rel2current_thresh,hop2_all_rel_conf_label_info,which_hop):
    correctness_index=4
    if(which_hop==1):
        relation_index=0
        conf_index=1
        filtering_rel_index=2
        filtering_conf_index=3
    elif(which_hop==2):
        relation_index=2
        conf_index=3
        filtering_rel_index=0
        filtering_conf_index=1
        
    tuned_rel2conf_label={}
    #hop2_all_rel_conf_label_info : [hop1_rel,hop1_conf,hop2_rel,hop2_conf,hop2_correctness,hop1_correctness,hop2_queryID,hop2_sf_norm]
    for rel_conf_label_info in hop2_all_rel_conf_label_info:
        rel_filtering=rel_conf_label_info[filtering_rel_index]
        conf_filtering=rel_conf_label_info[filtering_conf_index]
        if(conf_filtering<fixed_rel2current_thresh[rel_filtering]):
            continue
        rel=rel_conf_label_info[relation_index]
        conf=rel_conf_label_info[conf_index]
        correct_for_response=rel_conf_label_info[correctness_index]
        if(rel not in tuned_rel2conf_label):
            tuned_rel2conf_label[rel]=[]
        tuned_rel2conf_label[rel].append([conf,correct_for_response])


    tuned_rel2thresh_cw={}
    for rel in tuned_rel2conf_label:
        score_list=tuned_rel2conf_label[rel]
        score_list.sort(key=lambda x: x[0],reverse=True)
        
        thresh_cw=[]
        for conf,correct_for_response in score_list:
            if(len(thresh_cw)==0):
                thresh_cw.append([conf,[0,0]])
            elif (conf != thresh_cw[-1][0] ):
                thresh_cw.append( [conf,thresh_cw[-1][1][:] ] )
            update_cw(correct_for_response,thresh_cw[-1][1])
        tuned_rel2thresh_cw[rel]=thresh_cw
        
    return tuned_rel2thresh_cw

def tune_single_hop(tuned_rel2current_thresh,fixed_rel2current_thresh,hop2_all_rel_conf_label_info,which_hop,num_correct_gt_total,hop1_total_cw):
    tuned_rel2thresh_cw=single_hop_pooling(fixed_rel2current_thresh,hop2_all_rel_conf_label_info,which_hop)

    tuned_rel2current_cw,performance=compute_current_cw(tuned_rel2current_thresh, tuned_rel2thresh_cw ,num_correct_gt_total,hop1_total_cw)
    print performance
    performance=tune_threshold(tuned_rel2current_cw,tuned_rel2thresh_cw,tuned_rel2current_thresh,performance,num_correct_gt_total)

def compute_performance(correct,incorrect,total_correct):
    if(correct==0):
        precision=0
        recall=0
        F1=0
    else:
        precision=correct / float(incorrect+correct)
        recall=correct / float(total_correct)
        F1=2*precision*recall/(precision+recall)
    performance={'F1': F1, 'precision': precision, 'recall': recall, 'c': correct, 'w': incorrect}
    return performance

def compute_current_cw(rel2current_thresh,rel2thresh_cw,num_correct_gt,hop1_total_cw):
    rel2current_cw={}
    total_cw=[0,0]
    for rel in rel2thresh_cw:
        if(rel not in rel2current_thresh):
            rel2current_thresh[rel]=1
        thresh=rel2current_thresh[rel]
        last_cw=[0,0]
        for conf,cw in rel2thresh_cw[rel]:
            if(conf<thresh):
                break
            last_cw=cw    
        rel2current_cw[rel]=last_cw
        total_cw[0]+=last_cw[0]
        total_cw[1]+=last_cw[1]
    performance=compute_performance(total_cw[1]+hop1_total_cw[1],total_cw[0]+hop1_total_cw[0],num_correct_gt)

    return rel2current_cw,performance

def tune_threshold(rel2current_cw,rel2thresh_cw,rel2current_thresh,performance,num_correct_gt):
    total_correct=performance['c']
    total_incorrect=performance['w']
    hop1_correct=hop1_total_cw[1]
    hop1_incorrect=hop1_total_cw[0]
    for rel in rel2thresh_cw:
        other_correct=total_correct-rel2current_cw[rel][1]
        other_incorrect=total_incorrect-rel2current_cw[rel][0]
        thresh_F1=[]
        for conf,cw in rel2thresh_cw[rel]:
            new_c=other_correct+cw[1]
            new_w=other_incorrect+cw[0]
            performance=compute_performance(new_c,new_w,num_correct_gt)
            thresh_F1.append([ conf,performance['F1'],cw[1],cw[0] ])
        best_thresh,best_F1,best_c,best_w=max(thresh_F1,key=lambda x: x[1])
        rel2current_cw[rel]=[best_w,best_c]
        rel2current_thresh[rel]=best_thresh
        total_correct=best_c+other_correct
        total_incorrect=best_w+other_incorrect
    performance=compute_performance(total_correct,total_incorrect,num_correct_gt)
    print performance


def output_tuned_threshold(rel2current_thresh,tuned_params_path):
    with open(tuned_params_path,"w") as f_out:
        for rel in rel2current_thresh:
            f_out.write(rel+' '+str(rel2current_thresh[rel])+'\n')

def normalize_str(slot_filler):
    #return unicodedata.normalize('NFKD',unicode(slot_filler,"utf-8") ).encode('ASCII','ignore').lower()
    return slot_filler.lower()

def load_hop2_query(hop2_query_expanded_path):
    hop2_queryID2hop1_sf={}
    tree = ET.parse(hop2_query_expanded_path)
    root = tree.getroot()
    for child in root.findall('query'):
        hop2_queryID=child.attrib['id']
        hop1_sf=child[0].text
        hop1_sf_norm=normalize_str(hop1_sf)
        hop2_queryID2hop1_sf[hop2_queryID]=hop1_sf_norm

    return hop2_queryID2hop1_sf


def scoring_response(input_file_path,rel2query2sf2label_group,inv_rel_mapping):
    rel2query2sf_conf={}
    seen_group=set()
    query2rel={}
    total_cw=[0,0]
    with open(input_file_path,"r") as f_in:
    #with codecs.open(input_file_path,'r','utf-8') as f_in:
        for line in f_in:
            line=line.replace("\n","")
            #print line
            queryID,rel,teamID,provenance,slot_filler,filler_type,sf_prov,conf_score=line.split("\t")
            if(rel in inv_rel_mapping):
                rel=inv_rel_mapping[rel][0]
            if(rel not in rel2query2sf_conf):
                rel2query2sf_conf[rel]={}
            if(queryID not in rel2query2sf_conf[rel]):
                rel2query2sf_conf[rel][queryID]={}
            correct_for_response=UNASSESSED
            slot_filler_norm=normalize_str(slot_filler)
            if(queryID in rel2query2sf2label_group[rel] and slot_filler_norm in rel2query2sf2label_group[rel][queryID]):
                correct_for_classifier,correct_group=rel2query2sf2label_group[rel][queryID][slot_filler_norm]
                if(correct_group != '0' and correct_group in seen_group):
                    correct_for_classifier=DUPLICATION
                else:
                    seen_group.add(correct_group)
                correct_for_response=correct_for_classifier
            rel2query2sf_conf[rel][queryID][slot_filler_norm]=[ float(conf_score),correct_for_response ]
            #if(queryID=="CSSF15_ENG_ee5d2b1b9a_1126c5c420a6"):
            #    print rel2query2sf_conf[rel][queryID][slot_filler_norm]
            #if(queryID=="CSSF15_ENG_6b72c30a54"):
            #    print slot_filler_norm
            query2rel[queryID]=rel
            update_cw(correct_for_response,total_cw)
            #if(correct_for_response == CORRECT):
            #    total_cw[1]+=1
            #if(correct_for_response == WRONG or correct_for_response == PARENT_WRONG or correct_for_response == DUPLICATION):
            #    total_cw[0]+=1
    return rel2query2sf_conf,query2rel,total_cw


def hop2_queryID2hop1_queryID(hop2_queryID):
    hop1_end_index=hop2_queryID.rfind('_')
    hop1_queryID=hop2_queryID[:hop1_end_index]
    return hop1_queryID

def parent_incorrect_labeling(hop1_rel2query2sf_conf,hop2_rel2query2sf_conf,hop2_queryID2hop1_sf,hop1_query2rel):
    hop2_all_rel_conf_label_info=[]
    rel2num={}
    for hop2_rel in hop2_rel2query2sf_conf:
        if(hop2_rel not in rel2num):
            rel2num[hop2_rel]=defaultdict(int)

        for hop2_queryID in hop2_rel2query2sf_conf[hop2_rel]:
            hop1_sf_norm=hop2_queryID2hop1_sf[hop2_queryID]
            hop1_queryID=hop2_queryID2hop1_queryID(hop2_queryID)
            hop1_rel=hop1_query2rel[hop1_queryID]
            if(hop1_sf_norm not in hop1_rel2query2sf_conf[hop1_rel][hop1_queryID]):
                print "Ingoring ",hop1_sf_norm, ", because the mismatch between hop1 response and hop2 query file. The reason might be some special character problem"
                continue
            hop1_conf,hop1_correctness=hop1_rel2query2sf_conf[hop1_rel][hop1_queryID][hop1_sf_norm]
            
            for hop2_sf_norm in hop2_rel2query2sf_conf[hop2_rel][hop2_queryID]:
                hop2_conf,hop2_correctness=hop2_rel2query2sf_conf[hop2_rel][hop2_queryID][hop2_sf_norm]
                if(hop2_correctness != UNASSESSED and hop1_correctness == UNASSESSED):
                    print "Strange"
                    sys.exit(0)
                if(hop1_correctness == WRONG):
                    hop2_correctness = PARENT_WRONG
                hop2_all_rel_conf_label_info.append([hop1_rel,hop1_conf,hop2_rel,hop2_conf,hop2_correctness,hop1_correctness,hop2_queryID,hop2_sf_norm])
                #if(hop2_correctness not in rel2num):
                #    rel2num[hop2_correctness]=0
                rel2num[hop2_rel][hop2_correctness]+=1
            #if(hop2_queryID=="SSF15_ENG_ee5d2b1b9a_1126c5c420a6"):
            #    print hop2_correctness

    return hop2_all_rel_conf_label_info,rel2num

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

def create_output_folder(out_path):
    out_dir=os.path.dirname(out_path)
    if(not os.path.isdir(out_dir)):
        os.mkdir(out_dir)

if __name__ == '__main__':
    scored_postprocessed_file_path=sys.argv[1] #response_pp15_noNIL
    hop1_responses_path=sys.argv[2]

    hop2_query_path=sys.argv[3]
    assessment_file_path=sys.argv[4]
    rel_not_handled_path=sys.argv[5]
    inverse_mapping_path=sys.argv[6]
    
    initial_params_path=sys.argv[7]
    hop1_tuned_params_path=sys.argv[8]
    hop2_tuned_params_path=sys.argv[9]
    
    create_output_folder(hop1_tuned_params_path)
    create_output_folder(hop2_tuned_params_path)

    num_iter=int(sys.argv[10])

    rel2query2sf2label_group={}
    seen_correct_group=[set(),set()]

    inv_rel_mapping=load_inv_mapping(rel_not_handled_path,inverse_mapping_path)

    hop2_queryID2hop1_sf=load_hop2_query(hop2_query_path)

    with open(assessment_file_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            label_id,queryID_rel,provenance,slot_filler,sf_prov,ans1,ans2,correct_group=line.split("\t")
            hop_index=len(correct_group.split(':'))-2
            if(correct_group != '0'):
                seen_correct_group[hop_index].add(correct_group)
            queryID,rel=queryID_rel.split(":",1)
            if(rel in inv_rel_mapping):
                rel=inv_rel_mapping[rel][0]
            correct_for_classifier=WRONG
            if(ans1=='C' or ans2=='C'):
                correct_for_classifier=CORRECT
            if(rel not in rel2query2sf2label_group):
                rel2query2sf2label_group[rel]={}
            if(queryID not in rel2query2sf2label_group[rel]):
                rel2query2sf2label_group[rel][queryID]={}

            slot_filler_norm=normalize_str(slot_filler)
            if( slot_filler in rel2query2sf2label_group[rel][queryID] and rel2query2sf2label_group[rel][queryID][slot_filler_norm][0] !=  correct_for_classifier ):
                correct_for_classifier=CONTRADICT
            rel2query2sf2label_group[rel][queryID][slot_filler_norm]=[correct_for_classifier,correct_group]
    
    num_correct_gt_hop1=len(seen_correct_group[0])
    num_correct_gt_hop2=len(seen_correct_group[1])
    num_correct_gt_total=num_correct_gt_hop1+num_correct_gt_hop2
    
    hop1_rel2query2sf_conf,hop1_query2rel,hop1_total_cw=scoring_response(hop1_responses_path,rel2query2sf2label_group,inv_rel_mapping)
    hop2_rel2query2sf_conf,hop2_query2rel,hop2_total_cw=scoring_response(scored_postprocessed_file_path,rel2query2sf2label_group,inv_rel_mapping)
    
    print num_correct_gt_hop1, num_correct_gt_hop2
    print hop1_total_cw

    hop2_all_rel_conf_label_info,rel2num=parent_incorrect_labeling(hop1_rel2query2sf_conf,hop2_rel2query2sf_conf,hop2_queryID2hop1_sf,hop1_query2rel)

    #print hop2_rel2query2sf_all_conf_label

    total_stats=defaultdict(int)
    for rel in rel2num:
        print rel, rel2num[rel]
        for stats in rel2num[rel]:
            if( type(rel2num[rel][stats]) is not int):
                continue
            total_stats[stats]+=rel2num[rel][stats]
    print total_stats
    
    hop1_rel2current_thresh={}
    with open(initial_params_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            rel,thresh=line.split(' ')
            hop1_rel2current_thresh[rel]=float(thresh)
    
    hop2_rel2current_thresh=copy.deepcopy(hop1_rel2current_thresh)
    for i in range(num_iter):
        print "Interation ", i
        tune_single_hop(hop1_rel2current_thresh,hop2_rel2current_thresh,hop2_all_rel_conf_label_info,1,num_correct_gt_total,hop1_total_cw)
        tune_single_hop(hop2_rel2current_thresh,hop1_rel2current_thresh,hop2_all_rel_conf_label_info,2,num_correct_gt_total,hop1_total_cw)

    output_tuned_threshold(hop1_rel2current_thresh,hop1_tuned_params_path)
    output_tuned_threshold(hop2_rel2current_thresh,hop2_tuned_params_path)
