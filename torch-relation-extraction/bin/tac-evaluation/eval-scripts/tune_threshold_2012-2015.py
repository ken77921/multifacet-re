import sys
import os
import unicodedata
from collections import defaultdict

def deserialize_threshold_scores(threshold_score_path):
    num_correct_gt=0
    rel2thresh_cw={}
    with open(threshold_score_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            line_split=line.split("\t")
            if( len(line_split)==2 ):
                num_correct_gt+=float(line_split[1])
                continue
            rel,rel_org,conf,num_incorrect,num_correct=line_split
            #if(rel != rel_org):
            #    continue
            if(rel not in rel2thresh_cw):
                rel2thresh_cw[rel]=[]
            rel2thresh_cw[rel].append([ float(conf), [float(num_incorrect),float(num_correct)] ])

    rel2thresh_cw_acc={}
    for rel in rel2thresh_cw:
        score_list=rel2thresh_cw[rel]
        score_list.sort(reverse=True,key=lambda x:x[0])
        score_list_acc=[ [1,[0,0]] ]
        for conf, cw in score_list:
            new_cw=score_list_acc[-1][1][:]
            new_cw[0]+=cw[0]
            new_cw[1]+=cw[1]
            score_list_acc.append( [conf,new_cw] )
        rel2thresh_cw_acc[rel]=score_list_acc
    
    return rel2thresh_cw_acc,num_correct_gt

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

def compute_current_cw(rel2current_thresh,rel2thresh_cw_acc,num_correct_gt,init_recall):
    rel2current_cw={}
    total_cw=[0,0]
    for rel in rel2thresh_cw_acc:
        if(rel not in rel2current_thresh):
            rel2current_thresh[rel]=1
        thresh=rel2current_thresh[rel]
        last_cw=[0,0]
        for conf,cw in rel2thresh_cw_acc[rel]:
            if(conf<thresh):
                break
            last_cw=cw    
        rel2current_cw[rel]=last_cw
        total_cw[0]+=last_cw[0]
        total_cw[1]+=last_cw[1]
    if(init_recall != -1): #align the recall with the initialization
        num_correct_gt=total_cw[1]/init_recall
    performance=compute_performance(total_cw[1],total_cw[0],num_correct_gt)

    return rel2current_cw,performance,num_correct_gt

def tune_threshold(rel2current_cw,rel2thresh_cw_acc,rel2current_thresh,performance,num_correct_gt,num_iter,inv_rel_mapping,have_inv_lowest):
    total_correct=performance['c']
    total_incorrect=performance['w']
    for i in range(num_iter):
        print "Iteration", i
        for rel in rel2thresh_cw_acc:
            other_correct=total_correct-rel2current_cw[rel][1]
            other_incorrect=total_incorrect-rel2current_cw[rel][0]
            thresh_F1=[]
            #lowest_conf=0
            #if(rel in inv_rel_mapping):
            #    lowest_conf=have_inv_lowest
            
            #print rel, ' ', lowest_conf
            for conf,cw in rel2thresh_cw_acc[rel]:
                #if(conf < lowest_conf):
                if(conf < have_inv_lowest):
                    break
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

    return performance

def output_tuned_threshold(rel2current_thresh,tuned_params_path):
    with open(tuned_params_path,"w") as f_out:
        for rel in rel2current_thresh:
            f_out.write(rel+' '+str(rel2current_thresh[rel])+'\n')

def load_inv_mapping(inverse_mapping_path):
    inv_rel_mapping={}
    with open(inverse_mapping_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            rel,inv_rels_str=line.split('\t',1)
            inv_rel_mapping[rel]=inv_rels_str.split('\t')

    return inv_rel_mapping

            
#remember to lowercase
if __name__ == '__main__':
    threshold_score_path=sys.argv[1]
    initial_params_path=sys.argv[2]
    tuned_params_path=sys.argv[3]
    num_iter=int(sys.argv[4])
    inverse_mapping_path=sys.argv[5]
    have_inv_lowest=float(sys.argv[6])
    init_recall=-1
    if(len(sys.argv)==8):
        init_recall=float(sys.argv[7])

    out_dir=os.path.dirname(tuned_params_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    inv_rel_mapping=load_inv_mapping(inverse_mapping_path)
    #print inv_rel_mapping

    rel2thresh_cw_acc,num_correct_gt=deserialize_threshold_scores(threshold_score_path)

    #print rel2thresh_cw_acc

    rel2current_thresh={}
    with open(initial_params_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            rel,thresh=line.split(' ')
            rel2current_thresh[rel]=float(thresh)
    
    rel2current_cw,performance,num_correct_gt=compute_current_cw(rel2current_thresh,rel2thresh_cw_acc,num_correct_gt,init_recall)
    print performance
    performance=tune_threshold(rel2current_cw,rel2thresh_cw_acc,rel2current_thresh,performance,num_correct_gt,num_iter,inv_rel_mapping,have_inv_lowest)
    print performance['recall']
    output_tuned_threshold(rel2current_thresh,tuned_params_path)
