import sys
reload(sys) 
sys.setdefaultencoding('utf-8')
import unicodedata
from collections import defaultdict

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

def compute_current_cw(rel2current_thresh,rel2thresh_cw,num_correct_gt):
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
    performance=compute_performance(total_cw[1],total_cw[0],num_correct_gt)

    return rel2current_cw,performance

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

def tune_threshold(rel2current_cw,rel2thresh_cw,rel2current_thresh,performance,num_correct_gt,num_iter,lowest_threhold):
    total_correct=performance['c']
    total_incorrect=performance['w']
    for i in range(num_iter):
        print "Iteration", i
        for rel in rel2thresh_cw:
            other_correct=total_correct-rel2current_cw[rel][1]
            other_incorrect=total_incorrect-rel2current_cw[rel][0]
            thresh_F1=[]
            for conf,cw in rel2thresh_cw[rel]:
                if(conf<lowest_threhold):
                    break
                new_c=other_correct+cw[1]
                new_w=other_incorrect+cw[0]
                performance=compute_performance(new_c,new_w,num_correct_gt)
                thresh_F1.append([ conf,performance['F1'],cw[1],cw[0] ])
            if(len(thresh_F1)>0):
                best_thresh,best_F1,best_c,best_w=max(thresh_F1,key=lambda x: x[1])
            else:
                best_thresh=1
                best_F1=0
                best_c=0
                best_w=0
            rel2current_cw[rel]=[best_w,best_c]
            rel2current_thresh[rel]=best_thresh
            total_correct=best_c+other_correct
            total_incorrect=best_w+other_incorrect
        performance=compute_performance(total_correct,total_incorrect,num_correct_gt)
        print performance

    return performance

def output_tuned_threshold(rel2current_thresh,tuned_params_path):
    with open(tuned_params_path,"w") as f_out:
        for rel in rel2current_thresh:
            f_out.write(rel+' '+str(rel2current_thresh[rel])+'\n')

            
def normalize_str(slot_filler):
    return slot_filler.replace(" ","")
    #return unicodedata.normalize('NFKD',unicode(slot_filler,"utf-8") ).encode('ASCII','ignore').lower()

#remember to lowercase
if __name__ == '__main__':
    scored_postprocessed_file_path=sys.argv[1] #response_pp15_noNIL
    assessment_file_path=sys.argv[2]
    initial_params_path=sys.argv[3]
    tuned_params_path=sys.argv[4]
    num_iter=int(sys.argv[5])
    lowest_threhold=float(sys.argv[6])
    rel_not_handled_path=sys.argv[7]
    inverse_mapping_path=sys.argv[8]

    inv_rel_mapping=load_inv_mapping(rel_not_handled_path,inverse_mapping_path)

    rel2query2sf2label_group={}
    seen_correct_group=set()
    with open(assessment_file_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            label_id,queryID_rel,provenance,slot_filler,sf_prov,ans1,NAM,ans2,correct_group,NAM2=line.split("\t")
            hop_num=len(correct_group.split(':'))-1
            if(hop_num==2):
                continue
            if(correct_group != '0'):
                seen_correct_group.add(correct_group)
            queryID,rel=queryID_rel.split(":",1)
            correct_for_classifier=0
            if(ans1=='C' or ans2=='C'):
                correct_for_classifier=1
            inv_rel_list=[rel]
            if(rel in inv_rel_mapping):
                inv_rel_list=inv_rel_mapping[rel]
            for rel in inv_rel_list:
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
            inv_rel_list=[rel]
            if(rel in inv_rel_mapping):
                inv_rel_list=inv_rel_mapping[rel]
            for rel in inv_rel_list:
                if(rel not in rel2query_sf_conf):
                    rel2query_sf_conf[rel]=[]
                rel2query_sf_conf[rel].append([queryID,slot_filler,float(conf_score)])
    
    rel2thresh_cw={}
    rel2num={} #submitted ignored duplicated
    total_correct_count=0
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
        rel2num[rel]['contradiction']=0
        rel2num[rel]['duplicated']=0
        for qid,slot_filler,conf in score_list:
            #slot_filler_norm=slot_filler.lower()
            slot_filler_norm=normalize_str(slot_filler)
            #print qid
            #if(qid == "CSSF15_ENG_f4f118b34e"):
            #    print slot_filler_norm, ' ', conf
            if(rel not in rel2query2sf2label_group or qid not in rel2query2sf2label_group[rel] or slot_filler_norm not in rel2query2sf2label_group[rel][qid] ):
                rel2num[rel]['ignored']+=1
                continue
            correct_for_classifier,correct_group=rel2query2sf2label_group[rel][qid][slot_filler_norm]
            if(correct_for_classifier==-1): #contradictionary evidence in assessment file
                rel2num[rel]['contradiction']+=1
                continue
            
            answer_correct=1
            if( not correct_for_classifier or correct_group in seen_group):
                answer_correct=0
                if(correct_for_classifier and correct_group in seen_group):
                    rel2num[rel]['duplicated']+=1
                    print "duplicated ",slot_filler_norm
            else:
                seen_group.add(correct_group)

            if(len(thresh_cw)==0):
                thresh_cw.append([conf,[0,0]])
            elif (conf != thresh_cw[-1][0] ):
                thresh_cw.append( [conf,thresh_cw[-1][1][:] ] )
            thresh_cw[-1][1][answer_correct]+=1
            if(answer_correct==1):
                total_correct_count+=1
                print slot_filler_norm.encode('utf-8')
        rel2thresh_cw[rel]=thresh_cw
        
        print rel2num[rel]
    print "total correct count: ", total_correct_count

    total_stats=defaultdict(int)
    for rel in rel2num:
        for stats in rel2num[rel]:
            if( type(rel2num[rel][stats]) is not int):
                continue
            total_stats[stats]+=rel2num[rel][stats]
    print total_stats
    #print rel2thresh_cw['per:spouse']
    
    rel2current_thresh={}
    with open(initial_params_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            rel,thresh=line.split(' ')
            rel2current_thresh[rel]=float(thresh)
    
    rel2current_cw,performance=compute_current_cw(rel2current_thresh,rel2thresh_cw,num_correct_gt)
    print performance
    performance=tune_threshold(rel2current_cw,rel2thresh_cw,rel2current_thresh,performance,num_correct_gt,num_iter,lowest_threhold)

    output_tuned_threshold(rel2current_thresh,tuned_params_path)
