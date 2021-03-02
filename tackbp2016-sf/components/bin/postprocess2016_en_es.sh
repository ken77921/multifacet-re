#!/bin/sh
# postprocess.sh <response> <query_xml> <title_org_map> <response_postprocessed>
INPUT=$1
QUERYXML=$2
ORG_MAP=$3
OUTPUT=$4

LINKSTAT=`$TAC_ROOT/bin/get_expand_config.sh wikilinks /dev/null`
relconfig2015=$TAC_ROOT/config/relations_coldstart2015_new.config

echo "$LINKSTAT is used for removing duplications"

# Bring date into TIMEX2 format if possible.
correct_date=`mktemp` 
$TAC_ROOT/components/bin/run.sh run.DateNormalizer $INPUT $correct_date

# Remove redundancy according to anchor text heuristics.
# Convert formats.
$TAC_ROOT/components/bin/run.sh run.RedundancyEliminator_en_es $LINKSTAT $correct_date $QUERYXML $ORG_MAP \
| $TAC_ROOT/components/bin/run.sh run.RemoveSlots $QUERYXML $TAC_ROOT/resources/manual_annotation/disallowed_slots \
| $TAC_ROOT/components/bin/run.sh run.ConvertResponse2012To2015 $relconfig2015 \
> $OUTPUT

rm $correct_date

