package run;
import java.io.BufferedWriter;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.io.LineNumberReader;
import java.io.OutputStreamWriter;
import java.nio.charset.Charset;
import java.util.HashMap;
import java.util.Map;

import query.QueryList;
import query.QueryList.Query;
import util.Responses;

import com.google.common.collect.HashMultimap;
import com.google.common.collect.Multimap;

public class PredictionToResponse_inv {
      
/**
 * Prints out a response from a prediction file as it is e.g. produced by the
 * classifier.
 * No redundancy elimination whatsoever is done, so literally same slots may
 * be written out. Therefore, RedundancyEliminator needs to be called in order
 * to obtain a final response.
 * 
 * 2013 compatible.
 * 
 * TODO: testing.
 * 
 * @param args
 * @throws IOException
 */
public static void main(String[] args) throws IOException {
  if (args.length != 3) {
    // TODO: remove 'teamid' and use standard teamid 'lsv' throughout.
    //System.err.println("Response " +
    //    "<query_expanded_xml> <prediction> <team_id> <inverse_map_path>");
    System.err.println("Response " +
        "<query_expanded_xml> <prediction> <team_id>");
    return;
  }
  
  QueryList ql = new QueryList(args[0]);
  String predFn = args[1];
  String teamId = args[2];
  //String inverse_map_path = args[3];
  
  Responses r = new Responses(ql);

  //Map<String, String> rel2inv_map = new HashMap<String, String>();

  //BufferedReader br = new BufferedReader(new FileReader(inverse_map_path));
  //  for(String line; (line=br.readLine()) != null;){
  //      String[] fields = line.split("\t");
  //      rel2inv_map.put(fields[0],fields[1]);
  //  }
    
  
  LineNumberReader spredBr = new LineNumberReader(new FileReader(predFn));
  for (String line; (line = spredBr.readLine()) != null;) {
    String[] fields = line.split("\t");
    if (fields.length != 9) {
      throw new IllegalArgumentException("Unexpected line " + 
          spredBr.getLineNumber() + " in score file:\n" + line);
    }
    
    double score = Double.parseDouble(fields[8]);

    if (score > 0) {
        String qid,slot,relation;
      if( (fields[2].length()>=4 && fields[2].substring(0,4).equals("CSSF") ) && fields[2].contains("|") ){
        String[] qid_rel=fields[2].split("\\|");
        //qid = fields[2];
        qid = qid_rel[0];
        slot = fields[0];
        //relation = rel2inv_map.get(fields[1]);
        relation=qid_rel[1];
      }else{
        qid = fields[0];
        slot = fields[2];
        relation = fields[1];
      }
      //System.out.println(qid+", "+ relation);
      String sentenceId = fields[3];
      String tuple = qid + "\t" + relation;
      r.addResponse2012(qid, relation, teamId, sentenceId, slot, 0, 0, 0, 0, 
          score);
    }
  }
  spredBr.close();
  
  BufferedWriter outWriter = new BufferedWriter(
      new OutputStreamWriter(System.out, Charset.forName("UTF-8").newEncoder()));
  r.writeResponse(teamId, outWriter);
  outWriter.flush();
}
}
