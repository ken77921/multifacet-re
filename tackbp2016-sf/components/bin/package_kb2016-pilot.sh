#!/bin/bash
set -e

queryfile=$1
round1file=$2
round2file=$3
outputfile=$4

export PERL5LIB="$TAC_ROOT/components/tac2016-pilot/ColdStart/"

if [ "$#" -lt 5 ]; then
    docs=`$TAC_ROOT/bin/get_expand_config.sh doclengths`
else
    docs=$5
fi

rm -f response_packaged

pwd

echo "/opt/perl/bin/perl5.14.2 $TAC_ROOT/components/tac2016-pilot/ColdStart/CS-PackageOutput-MASTER.pl -docs $docs $queryfile $round1file $round2file $outputfile"

/opt/perl/bin/perl5.14.2 $TAC_ROOT/components/tac2016-pilot/ColdStart/CS-PackageOutput-MASTER.pl -docs $docs $queryfile $round1file $round2file $outputfile
