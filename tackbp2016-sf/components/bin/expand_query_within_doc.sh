#!/bin/sh
# expand_query.sh <query_xml> <expanded_query_xml>
# Author: Benjamin Roth

RELLIST=`$TAC_ROOT/bin/get_expand_config.sh rellist $TAC_ROOT/config/rellist`
RELCONFIG=`$TAC_ROOT/bin/get_expand_config.sh relations.config $TAC_ROOT/config/relations.config`
LINKSTATS=`$TAC_ROOT/bin/get_expand_config.sh wikilinks /dev/null`
REDIRSTATS_EN=/iesl/canvas/proj/tackbp/2016-pilot/redirectAliasesEN
REDIRSTATS_SP=/iesl/canvas/proj/tackbp/2016-pilot/redirectAliasesSP
LINKBACK_EN=/iesl/canvas/proj/tackbp/2016-pilot/redirectLinkBackEN
LINKBACK_SP=/iesl/canvas/proj/tackbp/2016-pilot/redirectLinkBackSP
LANGLINK=/iesl/canvas/proj/tackbp/2016-pilot/enwiki-20160305-langlinks.tsv
ORG_SUFFIXES=$TAC_ROOT/resources/expansion/org_suffixes

precision_expansion=`$TAC_ROOT/bin/get_config.sh precision_expansion true`

#Expand <query_xml> <relations> <relation_config> <expansions> <redirect_eng> <redirect_spa> <linkback_eng> <linkback_spa> <language_link> <maxN> <expanded.xml>
$TAC_ROOT/components/bin/run.sh run.ExpandForWithinDocumentRetrieval $1 $RELLIST $RELCONFIG $LINKSTATS $REDIRSTATS_EN $REDIRSTATS_SP $LINKBACK_EN $LINKBACK_SP $LANGLINK 10 $ORG_SUFFIXES $2 $precision_expansion
