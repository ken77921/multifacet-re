#!/bin/bash
set -e

export PERL5LIB="$TAC_ROOT/components/tac2016-pilot/ColdStart/"

/opt/perl/bin/perl5.14.2 $TAC_ROOT/components/tac2016-pilot/ColdStart/CS-GenerateQueries-MASTER.pl $@


