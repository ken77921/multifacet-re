import sys
import unicodedata
from collections import defaultdict

def serialize_output_to_file(rel2thresh_cw,scoring_output_path,num_correct_gt,inv_rel_mapping):
    delim='\t'
    with open(scoring_output_path,"w") as f_out:
        f_out.write("number of correct ground truth" + delim + str(num_correct_gt)+'\n')
        for rel in rel2thresh_cw:
            if(rel in inv_rel_mapping):
                inv_rel=inv_rel_mapping[rel][0]
            else:
                inv_rel=rel
            for conf,cw in rel2thresh_cw[rel]:
                f_out.write(inv_rel+delim+rel+delim+str(conf)+delim+str(cw[0])+delim+str(cw[1])+'\n')

def normalize_str(slot_filler):
    #return unicodedata.normalize('NFKD',unicode(slot_filler,"utf-8") ).encode('ASCII','ignore').lower()
    return slot_filler.lower()

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

#remember to lowercase
if __name__ == '__main__':
    scored_postprocessed_file_path=sys.argv[1] #response_pp15_noNIL
    assessment_file_path=sys.argv[2]
    scoring_output_path=sys.argv[3]
    rel_not_handled_path=sys.argv[4]
    inverse_mapping_path=sys.argv[5]

    rel2query2sf2label_group={}
    seen_correct_group=set()
    seen_prov_sf_rel=set()
    with open(assessment_file_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            label_id,queryID_rel,provenance,slot_filler,sf_prov,ans1,ans2,correct_group=line.split("\t")
            hop_num=len(correct_group.split(':'))-1
            if(hop_num==2):
                continue
            queryID,rel=queryID_rel.split(":",1)
            prov_sf_rel=provenance+sf_prov+slot_filler+rel
            if(prov_sf_rel in seen_prov_sf_rel):
                continue
            seen_prov_sf_rel.add(prov_sf_rel)
            if(correct_group != '0'):
                seen_correct_group.add(correct_group)
            correct_for_classifier=0
            if(ans1=='C' or ans2=='C'):
                correct_for_classifier=1
            if(rel not in rel2query2sf2label_group):
                rel2query2sf2label_group[rel]={}
            if(queryID not in rel2query2sf2label_group[rel]):
                rel2query2sf2label_group[rel][queryID]={}

            #slot_filler_norm=slot_filler.lower()
            slot_filler_norm=normalize_str(slot_filler)
            if( slot_filler in rel2query2sf2label_group[rel][queryID] and rel2query2sf2label_group[rel][queryID][slot_filler_norm][0] !=  correct_for_classifier ):
                correct_for_classifier=-1
            rel2query2sf2label_group[rel][queryID][slot_filler_norm]=[correct_for_classifier,correct_group]
    
    num_correct_gt=len(seen_correct_group)
    
    rel2query_sf_conf={}
    with open(scored_postprocessed_file_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            #print line
            queryID,rel,teamID,provenance,slot_filler,filler_type,sf_prov,conf_score=line.split("\t")
            if(rel not in rel2query_sf_conf):
                rel2query_sf_conf[rel]=[]
            rel2query_sf_conf[rel].append([queryID,slot_filler,float(conf_score)])
    
    rel2thresh_cw={}
    rel2num={} #submitted ignored duplicated
    for rel in rel2query_sf_conf:
        score_list=rel2query_sf_conf[rel]
        score_list.sort(key=lambda x: x[2],reverse=True)
        #if(rel=='per:spouse'):
        #    print score_list[:100]
        thresh_cw=[]
        seen_group=set()
        rel2num[rel]={}
        rel2num[rel]['relation']=rel
        rel2num[rel]['submitted']=len(score_list)
        rel2num[rel]['ignored']=0
        rel2num[rel]['controdiction']=0
        rel2num[rel]['duplicated']=0
        for qid,slot_filler,conf in score_list:
            #slot_filler_norm=slot_filler.lower()
            slot_filler_norm=normalize_str(slot_filler)
            #print qid
            #if(qid == "CSSF15_ENG_f4f118b34e"):
            #    print slot_filler_norm, ' ', conf
            if( qid not in rel2query2sf2label_group[rel] or slot_filler_norm not in rel2query2sf2label_group[rel][qid] ):
                rel2num[rel]['ignored']+=1
                continue
            correct_for_classifier,correct_group=rel2query2sf2label_group[rel][qid][slot_filler_norm]
            if(correct_for_classifier==-1): #contradictionary evidence in assessment file
                rel2num[rel]['controdiction']+=1
                continue
            
            answer_correct=1
            if( not correct_for_classifier or correct_group in seen_group):
                answer_correct=0
                if(correct_for_classifier and correct_group in seen_group):
                    rel2num[rel]['duplicated']+=1
            else:
                seen_group.add(correct_group)

            if(len(thresh_cw)==0):
                thresh_cw.append([conf,[0,0]])
            elif (conf != thresh_cw[-1][0] ):
                #thresh_cw.append( [conf,thresh_cw[-1][1][:] ] )
                thresh_cw.append( [conf,[0,0] ] )
            thresh_cw[-1][1][answer_correct]+=1
            rel2thresh_cw[rel]=thresh_cw
        
        print rel2num[rel]

    total_stats=defaultdict(int)
    for rel in rel2num:
        for stats in rel2num[rel]:
            if( type(rel2num[rel][stats]) is not int):
                continue
            total_stats[stats]+=rel2num[rel][stats]
    print total_stats
    #print rel2thresh_cw['per:spouse']
    
    inv_rel_mapping=load_inv_mapping(rel_not_handled_path,inverse_mapping_path)
    serialize_output_to_file(rel2thresh_cw,scoring_output_path,num_correct_gt,inv_rel_mapping)
