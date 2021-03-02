#!/bin/sh
# expand_query.sh <query_xml> <expanded_query_xml>
# Author: Benjamin Roth

RELLIST=`$TAC_ROOT/bin/get_expand_config.sh rellist $TAC_ROOT/config/rellist`
RELCONFIG=`$TAC_ROOT/bin/get_expand_config.sh relations.config $TAC_ROOT/config/relations.config`
LINKSTATS=`$TAC_ROOT/bin/get_expand_config.sh wikilinks /dev/null`
REDIRSTATS_EN=`$TAC_ROOT/bin/get_expand_config.sh redirect_en /dev/null`
REDIRSTATS_SP=`$TAC_ROOT/bin/get_expand_config.sh redirect_sp /dev/null`
LINKBACK_EN=`$TAC_ROOT/bin/get_expand_config.sh linkback_en /dev/null`
LINKBACK_SP=`$TAC_ROOT/bin/get_expand_config.sh linkback_sp /dev/null`
LANGLINK=`$TAC_ROOT/bin/get_expand_config.sh langlink /dev/null`
ORG_SUFFIXES=$TAC_ROOT/resources/expansion/org_suffixes

echo $LINKSTATS
echo $REDIRSTATS_EN
echo $REDIRSTATS_EN
echo $LINKBACK_EN
echo $LINKBACK_SP
echo $LANGLINK

precision_expansion=`$TAC_ROOT/bin/get_config.sh precision_expansion true`

#Expand <query_xml> <relations> <relation_config> <expansions> <redirect_eng> <redirect_spa> <linkback_eng> <linkback_spa> <language_link> <maxN> <expanded.xml>
$TAC_ROOT/components/bin/run.sh run.Expand $1 $RELLIST $RELCONFIG $LINKSTATS $REDIRSTATS_EN $REDIRSTATS_SP $LINKBACK_EN $LINKBACK_SP $LANGLINK 10 $ORG_SUFFIXES $2 $precision_expansion
