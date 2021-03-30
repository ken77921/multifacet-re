# Multi-facet Universal Schema

## Data preparation and training
`cd multifacet_relation_extraction`
Follow the instructions in `multifacet_relation_extraction/README.md`

## Evaluation of TAC
In order to follow the evaluation procedure in Verga et al., 2016, we need to perform following steps

Step1: cd to this repo. Set up the path using
```
export TAC_ROOT=`pwd`/tackbp2016-sf
export TH_RELEX_ROOT=`pwd`/torch-relation-extraction
```

Step2: Download and unzip the [libraries](https://drive.google.com/file/d/1ljuUaqPj4e4G--WktcOpGAWZ-22Yn577/view?usp=sharing) needed for compiling the JAVA Code into 
`tackbp2016-sf/components/pipeline/`. To compile the JAVA code in `./tackbp2016-sf`, assuming your jdk path is `/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.275.b01-0.el7_9.x86_64`, you can run:
```
export JAVA_HOME="/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.275.b01-0.el7_9.x86_64"
cd tackbp2016-sf
./components/pipeline/build.sh
```

Step3: Compile java codes in `./torch-relation-extraction`
```
cd torch-relation-extraction
./setup-tac-eval.sh
```

Step4: 
- Download [this zip file](https://drive.google.com/file/d/1v0YxDXzKxzO9a-LRQ_5lVxTXMN9k2sfZ/view?usp=sharing) and extract the `data` folder into `./torch-relation-extraction`. 
- In `./torch-relation-extraction`, run:  
```./bin/tac-evaluation/test_all_NSD_formal_release.sh ../multifacet_relation_extraction/results/milestone_run_trans-b5-kb11_trans_results```
Then, the final scores will be stored in `../multifacet_relation_extraction/results/milestone_run_trans-b5-kb11_trans_results`.

**NOTE:** We store the results of several different scoring functions in 
`../multifacet_relation_extraction/results/milestone_run_trans-b5-kb11` by default, 
which will make `./bin/tac-evaluation/test_all_NSD_formal_release.sh` take a long time to finish. 
In order to make the code run faster, you can only keep the folder `*_kmeans_avg` in 
`../multifacet_relation_extration/results/milestone_run_trans-b5-kb11_trans_results`, which stores the results we report in our paper.

## F1 Score reported in our paper
To view the F1 score, run the jupyter notebook `results/Results.ipynb`.

## Citation
If you use the codes in `multifacet_relation_extraction` for your paper, please cite [Paul et al., 2021](http://arxiv.org/abs/2103.15339).

If you use the training data or codes in `torch-relation-extraction`, please cite Verga et al., 2016.

If you use the codes in `tackbp2016-sf` to perform slot filling, please cite Chang et al., 2016.

```
Rohan Paul*, Haw-Shiuan Chang*, and Andrew McCallum,
"Multi-facet Universal Schema."
Conference of the European Chapter of the Association for Computational Linguistics (EACL), 2021

Patrick Verga, David Belanger, Emma Strubell, Benjamin Roth, and Andrew McCallum,
"Multilingual Relation Extraction using Compositional Universal Schema."
Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (HLT/NAACL), 2016

Haw-Shiuan Chang, Abdurrahman Munir, Ao Liu, Johnny Tian-Zheng Wei, Aaron Traylor, Ajay Nagesh, Nicholas Monath, Patrick Verga, Emma Strubell, and Andrew McCallum,
"Extracting Multilingual Relations under Limited Resources: TAC 2016 Cold-Start KB construction and Slot-Filling using Compositional Universal Schema."
Text Analysis Conference, Knowledge Base Population (TAC/KBP), 2016
```
