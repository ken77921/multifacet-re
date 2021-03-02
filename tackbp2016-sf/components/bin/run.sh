#!/bin/sh
LOG4J=file://$TAC_ROOT/config/log4j.config

HAVE_SPACE_DIR=$TEMP_FOLDER

COMP=$TAC_ROOT/components/pipeline/
#JAVA_HOME=$TAC_ROOT/lib/java/jdk1.6.0_18/
#echo "java -Djava.io.tmpdir=$HAVE_SPACE_DIR  -Dfile.encoding=UTF8 -Dlog4j.configuration=$LOG4J -cp $COMP/dist/components.jar:$COMP/lib/* -Xmx32g $@"
#/usr/java/latest/bin/java -Djava.io.tmpdir=$HAVE_SPACE_DIR  -Dfile.encoding=UTF8 -Dlog4j.configuration=$LOG4J -cp $COMP/dist/components.jar:$COMP/lib/* -Xmx32g $@
java -Djava.io.tmpdir=$HAVE_SPACE_DIR  -Dfile.encoding=UTF8 -Dlog4j.configuration=$LOG4J -cp $COMP/dist/components.jar:$COMP/lib/* -Xmx32g $@
