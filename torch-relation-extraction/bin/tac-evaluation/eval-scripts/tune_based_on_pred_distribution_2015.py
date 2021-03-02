import sys
import unicodedata
from collections import defaultdict
import pickle

def search_acc(conf_acc,conf_now,largest_index):
    for i in range(largest_index,-len(conf_acc)-1,-1):
        conf,acc=conf_acc[i]
        if(conf<=conf_now):
            accuracy_at_conf_now=acc
            break
    return accuracy_at_conf_now,i

def serialize_KDE_output_to_file(KDE_output_path,inv_rel_mapping,rel2conf_dist,rel_conf_acc):
    delim='\t'
    with open(KDE_output_path,"w") as f_out:
        num_correct_acc=0
        for rel in rel2conf_dist:
            if(rel in inv_rel_mapping):
                inv_rel=inv_rel_mapping[rel][0]
            else:
                inv_rel=rel
            
            conf_acc=[]
            for rel_test,conf_acc_test in rel_conf_acc:
                if( inv_rel == rel_test ):
                    conf_acc=conf_acc_test
                    break
            if(len(conf_acc)==0):
                continue
            
            largest_index=-1
            for conf_now in rel2conf_dist[rel]:
                #accuracy_at_conf_now=[accuracy  for conf,accuracy in conf_acc if conf>=conf_now][0]
                accuracy_at_conf_now,largest_index=search_acc(conf_acc,conf_now,largest_index)
                #correct_num=min(accuracy_at_conf_now,conf_now)
                correct_num=accuracy_at_conf_now
                incorrect_num=1-accuracy_at_conf_now
                num_correct_acc+=correct_num
                f_out.write(inv_rel+delim+rel+delim+str(conf_now)+delim+str(incorrect_num)+delim+str(correct_num)+'\n')
        #num_correct_acc*=2
        f_out.write("number of correct response" + delim + str(num_correct_acc)+'\n')


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
    rel_not_handled_path=sys.argv[2]
    inverse_mapping_path=sys.argv[3]
    KDE_accuracy_path=sys.argv[4]
    KDE_output_path=sys.argv[5]

    rel_conf_acc=pickle.load( open(KDE_accuracy_path,'r') )
   
    rel2conf_dist={}
    with open(scored_postprocessed_file_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            #print line
            queryID,rel,teamID,provenance,slot_filler,filler_type,sf_prov,conf_score=line.split("\t")
            if(rel not in rel2conf_dist):
                rel2conf_dist[rel]=[]
            rel2conf_dist[rel].append(float(conf_score))
    
    rel2thresh_cw={}
    rel2num={} #submitted ignored duplicated
    for rel in rel2conf_dist:
        score_list=rel2conf_dist[rel]
        score_list.sort(reverse=True)
        
    #print rel2thresh_cw['per:spouse']
    
    inv_rel_mapping=load_inv_mapping(rel_not_handled_path,inverse_mapping_path)

    serialize_KDE_output_to_file(KDE_output_path,inv_rel_mapping,rel2conf_dist,rel_conf_acc)
