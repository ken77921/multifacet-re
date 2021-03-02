import sys
import unicodedata
from collections import defaultdict

def serialize_output_to_file(rel2thresh_cw,scoring_output_path,num_correct_gt):
    delim='\t'
    with open(scoring_output_path,"w") as f_out:
        f_out.write("number of correct ground truth" + delim + str(num_correct_gt)+'\n')
        for rel in rel2thresh_cw:
            for conf,cw in rel2thresh_cw[rel]:
                f_out.write(rel+delim+rel+delim+str(conf)+delim+str(cw[0])+delim+str(cw[1])+'\n')

def normalize_str(slot_filler):
#    return unicodedata.normalize('NFKD',unicode(slot_filler,"utf-8") ).encode('ASCII','ignore').lower()
    return slot_filler.lower()


def load_key_file(assessment_file_path,year):
    rel2query2sf2label_group={}
    seen_correct_group=set()
    with open(assessment_file_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")

            correct_for_classifier=0
            if(year==2012):
                label_id,queryID,doc_id, ans1, correct_group_raw, slot_filler,ans_raw, slot_filler_raw,ans2,prov=line.split("\t")
                queryID_prefix,rel=queryID.split(":",1)
                
                if(ans1=='1' or ans2=='1'):
                    correct_for_classifier=1
            elif(year==2013):
                label_id, queryID, doc_id, slot_filler, start_end_sf, start_end_arg1 , start_end_prov, anws_sf, anws_arg1, anws_rel, anws_all, correct_group_raw=line.split("\t")
                queryID_prefix,rel=queryID.split(":",1)
            
                if(anws_sf=='C' or anws_rel=='C' or anws_all=='C' ):
                    correct_for_classifier=1
            elif(year==2014):
                label_id, queryID, prov_rel, slot_filler, prov_sf, anws_sf, anws_rel, correct_group_raw=line.split("\t")
                queryID_prefix,rel=queryID.split(":",1)
            
                if(anws_sf=='C' or anws_rel=='C' ):
                    correct_for_classifier=1
                
            correct_group=queryID+':'+correct_group_raw
            if(correct_group_raw != '0'):
                seen_correct_group.add(correct_group)
                
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
    return rel2query2sf2label_group,num_correct_gt

def load_scored_candidates(scoring_postprocessed_fil_path,year):
    rel2query_sf_conf={}
    with open(scored_postprocessed_file_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            #print line
            if(year==2012):
                queryID_prefix,rel,teamID,provenance,slot_filler,start_sf,end_sf,start_prov,end_prov,conf_score=line.split("\t")
            elif(year==2013):
                queryID_prefix,rel,teamID,doc_id,slot_filler,start_end_sf,start_end_arg1,start_end_prov,conf_score=line.split("\t")
            elif(year==2014):
                queryID_prefix,rel,teamID,prov_rel,slot_filler,prov_rel,conf_score=line.split("\t")

            queryID=queryID_prefix+':'+rel

            if(rel not in rel2query_sf_conf):
                rel2query_sf_conf[rel]=[]
            rel2query_sf_conf[rel].append([queryID,slot_filler,float(conf_score)])
    
    return rel2query_sf_conf


if __name__ == '__main__':
    scored_postprocessed_file_path=sys.argv[1] #response_pp15_noNIL
    assessment_file_path=sys.argv[2]
    scoring_output_path=sys.argv[3]
    year=int(sys.argv[4])
    
    rel2query2sf2label_group,num_correct_gt=load_key_file(assessment_file_path,year)
    
    rel2query_sf_conf=load_scored_candidates(scored_postprocessed_file_path,year)
    
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
    
    serialize_output_to_file(rel2thresh_cw,scoring_output_path,num_correct_gt)
