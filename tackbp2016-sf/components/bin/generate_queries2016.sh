#!/bin/bash
set -e

export PERL5LIB="$TAC_ROOT/evaluation/bin/2016_04/"

/opt/perl/bin/perl5.14.2 $TAC_ROOT/evaluation/bin/2016_04/CS-GenerateQueries-MASTER.pl $@


