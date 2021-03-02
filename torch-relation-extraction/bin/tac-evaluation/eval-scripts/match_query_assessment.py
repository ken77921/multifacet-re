import sys
import unicodedata
from collections import defaultdict
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def normalize_str(slot_filler):
    #return unicodedata.normalize('NFKD',unicode(slot_filler,"utf-8") ).encode('ASCII','ignore').lower()
    return slot_filler.lower()

if __name__ == '__main__':
    scored_input_file_path=sys.argv[1]
    assessment_file_path=sys.argv[2]
    query_file_path=sys.argv[3]
    scored_output_file_path=sys.argv[4]

    query2ent1={}
    current_query=""
    with open(query_file_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            query_header='<query id="'
            query_start = line.find(query_header)
            if(query_start != -1):
                query_end = line.find('">')
                current_query=line[query_start+len(query_header):query_end]
            name_header='<name>'
            ent1_start = line.find(name_header)
            if(ent1_start != -1):
                ent1_end = line.find('</name>')
                current_ent1=line[ent1_start+len(name_header):ent1_end]
                query2ent1[current_query]=current_ent1

    #print query2ent1
    
    rel2query2sf2label_group={}
    with open(assessment_file_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            label_id,queryID_rel,provenance,slot_filler,sf_prov,ans1,ans2,correct_group=line.split("\t")
            hop_num=len(correct_group.split(':'))-1
            if(hop_num==2):
                continue
            queryID,rel=queryID_rel.split(":",1)
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
    
    
    f_out=open(scored_output_file_path,"w")
    with open(scored_input_file_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            #print line
            line_split=line.split("\t")
            #print line
            if(len(line_split)==4):
                f_out.write(line+"\n")
            else:
                queryID,rel,teamID,provenance,slot_filler,dumpy1,dumpy2,dump3,dump4,conf_score=line_split
                slot_filler_norm=normalize_str(slot_filler)
                answer="Unassessed"
                if( queryID in rel2query2sf2label_group[rel] and slot_filler_norm in rel2query2sf2label_group[rel][queryID] ):
                    correctness=rel2query2sf2label_group[rel][queryID][slot_filler_norm][0]
                    answer=bcolors.OKGREEN+"Correct"+bcolors.ENDC if correctness else bcolors.FAIL+"Wrong"+bcolors.ENDC
                ent1=query2ent1[queryID]
                
                doc_prov,raw_text=provenance.split("|",1)

                out_list=[queryID,teamID,bcolors.BOLD+ent1,rel,slot_filler+bcolors.ENDC,bcolors.WARNING+conf_score+bcolors.ENDC,raw_text,doc_prov,answer]
                f_out.write( "\t".join(out_list)+"\n")
    
    f_out.close()
