import sys

if __name__ == '__main__':
    input_file=sys.argv[1]
    map_file=sys.argv[2]
    output_file=sys.argv[3]
    rel2inv_list={}
    with open(map_file,"r") as f_in:
        for line in f_in:
            #print line
            line=line.replace("\n","")
            if(len(line)==0):
                continue
            rel,inv_rel_str=line.split('\t',1)
            inv_rel_list=inv_rel_str.split('\t')
            rel2inv_list[rel]=inv_rel_list
            #for inv_rel in inv_rel_list:
            #    rel2inv[rel]=inv_rel
    #print rel2inv
    f_out=open(output_file,"w")
    with open(input_file,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            e2,rel,query_id,rest=line.split('\t',3)
            if(rel not in rel2inv_list):
                print "Does not recognize relation: ", rel
                continue
            for inv_rel in rel2inv_list[rel]:
                output_list=[e2,inv_rel,query_id+"|"+rel,rest]
                f_out.write( "\t".join(output_list)+"\n" )
    f_out.close()
