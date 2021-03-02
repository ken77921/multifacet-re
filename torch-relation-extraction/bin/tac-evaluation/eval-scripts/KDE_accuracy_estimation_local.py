import csv 
import numpy as np
#import matplotlib.pyplot as plt 
from sklearn.neighbors import KernelDensity
import pickle
import sys

def load_inv_mapping(inverse_mapping_path):
    inv_rel_mapping={}
    with open(inverse_mapping_path,"r") as f_in:
        for line in f_in:
            line=line.replace("\n","")
            rel,inv_rels_str=line.split('\t',1)
            inv_rel_mapping[rel]=inv_rels_str.split('\t')

    return inv_rel_mapping

#scoring_output_path='/Users/ken77921/Desktop/data/USchema_SES_scoring_output'
scoring_output_path=sys.argv[1]

#inv_map_path="/Users/ken77921/Desktop/codes/tackbp2016-kb/config/coldstart_relations2015_inverses.config"
inv_map_path=sys.argv[2]

KDE_estimation_output=sys.argv[3]

inv_rel_mapping=load_inv_mapping(inv_map_path)

with open(scoring_output_path) as fh: 
    file = list(csv.reader(fh,delimiter='\t'))

dick = {}
for row in file:
    if(len(row)<4):
        continue
    if row[0] not in dick:
        dick[row[0]] = ([],[])

    #print row

    allpt = dick[row[0]][0]
    incorrect = dick[row[0]][1]
    incorrect.extend([ float(row[2]) ] * int(row[4]))
    allpt.extend( [ float(row[2]) ] * (int(row[3])+int(row[4])))
#print dick
estimations = []
for relation,points in dick.iteritems():
    print relation
    X = np.array( points[1] )[:,np.newaxis]
    Y = np.array( points[0] )[:,np.newaxis]

    #plt.scatter(Y,[0] * len(Y))#np.random.normal(0,0.03,len(Y)))
    #plt.scatter(X,[1] * len(X))#np.random.normal(1,0.03,len(X)))
    #plt.title(relation)
    #plt.ylabel("Correctness")
    #plt.xlabel("Confidence")

    #kde
    X_plot = np.linspace(0,1,1000)[:,np.newaxis]
    kde_incorrect = KernelDensity(kernel='gaussian', bandwidth=0.15).fit(X)
    kde_allpt = KernelDensity(kernel='gaussian', bandwidth=0.15).fit(Y)

    log_dens_incorrect = kde_incorrect.score_samples(X_plot)
    log_dens_allpt = kde_allpt.score_samples(X_plot)

    #ax = plt.gca()
    estimation = np.exp(np.subtract(log_dens_incorrect + np.log(len(X)),log_dens_allpt + np.log(len(Y)))) 
    #ax.plot(X_plot, estimation)

    for i in range(0,len(estimation)-1):
        if estimation[i] > estimation[i+1]:
            estimation[i+1] = estimation[i]
    
    lin = np.linspace(0,1,1000)    
    if(relation in inv_rel_mapping):
        for i in range(0,len(estimation)-1):
            if(lin[i]>estimation[i]):
                break
            estimation[i] = min(estimation[i],lin[i])

    #ax.plot(X_plot, estimation)
    #plt.show()

    #output to pickle

    assert len(estimation) == len(lin)
    estimations.append((relation,zip(lin,estimation)))

pickle.dump(estimations,open(KDE_estimation_output,'w'))
