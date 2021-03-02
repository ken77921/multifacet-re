#!/usr/bin/env bash

YEAR=$1
PP=$2
QUERY_EXPANDED=$3
RESPONSE=$4
RESPONSE_PP=$5

echo "Post processing for year $YEAR"
#export TAC_CONFIG=$TAC_ROOT/config/coldstart2015_UMass_IESL1.config
export TAC_CONFIG=$TAC_ROOT/config/coldstart2015_updated.config
if [[ $PP == "pp14" ]]; then
  $TAC_ROOT/components/bin/postprocess2014.sh $RESPONSE $QUERY_EXPANDED /dev/null $RESPONSE_PP
elif [[ $PP == "pp13" ]]; then
  $TAC_ROOT/components/bin/postprocess2013.sh $RESPONSE $QUERY_EXPANDED /dev/null $RESPONSE_PP
elif [[ $PP == "pp13_es" ]]; then
  export TAC_CONFIG=$TAC_ROOT/config/coldstart2016_es_run4.config
  $TAC_ROOT/components/bin/postprocess2013.sh $RESPONSE $QUERY_EXPANDED /dev/null $RESPONSE_PP
elif [[ $PP == "pp15" ]]; then
  $TAC_ROOT/components/bin/postprocess2015.sh $RESPONSE $QUERY_EXPANDED /dev/null $RESPONSE_PP
elif [[ $PP == "pp15_es" ]]; then
  export TAC_CONFIG=$TAC_ROOT/config/coldstart2016_es_run4.config
  $TAC_ROOT/components/bin/postprocess2015.sh $RESPONSE $QUERY_EXPANDED /dev/null $RESPONSE_PP
elif [[ $PP == "pp12" ]]; then
    COMP=$TAC_ROOT/components/pipeline/
    LINKSTAT=/dev/null
    #LINKSTAT=/iesl/canvas/beroth/tac/data/relationfactory_models/expansion/enwiki.linktext.counts
    #JAVA_HOME=$TAC_ROOT/lib/java/jdk1.6.0_18/
    $TAC_ROOT/components/bin/run.sh run.RedundancyEliminator $LINKSTAT $RESPONSE $QUERY_EXPANDED > $RESPONSE_PP
else
  cp $RESPONSE $RESPONSE_PP
fi
