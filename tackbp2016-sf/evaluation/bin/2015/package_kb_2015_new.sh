#!/bin/bash
set -e

queryfile=$1
round1file=$2
round2file=$3
outputfile=$4

docs=`$TAC_ROOT/bin/get_expand_config.sh doclengths`
rm -f response_packaged

pwd

echo "/opt/perl/bin/perl5.14.2 -I $TAC_ROOT/evaluation/bin/2015/ $TAC_ROOT/evaluation/bin/2015/CS-PackageOutput-MASTER.pl -docs $docs $queryfile $round1file $round2file $outputfile"

/opt/perl/bin/perl5.14.2 -I $TAC_ROOT/evaluation/bin/2015/ $TAC_ROOT/evaluation/bin/2015/CS-PackageOutput-MASTER.pl -docs $docs $queryfile $round1file $round2file $outputfile
