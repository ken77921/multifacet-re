import java.lang.Integer;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileNotFoundException;

import java.util.HashMap;
import java.util.ArrayList;
import java.util.HashSet;

import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.queryParser.ParseException;
import org.apache.lucene.queryParser.QueryParser;
import org.apache.lucene.search.BooleanClause.Occur;
import org.apache.lucene.search.BooleanQuery;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;

public class compareLucene{

    public static void main(String[] args) throws IOException, ParseException {
        String queryXMLFn = args[0];
	String queryXMLFn2 = args[1];
        Directory dir = FSDirectory.open(new File("/iesl/canvas/aimunir/tackbp2016-sf/runs/coldstart2016_pilot_eng_UMass_IESL3.6/index"));
        IndexSearcher is = new IndexSearcher(dir, true);
        QueryParser parser = new QueryParser(Version.LUCENE_29, "contents",
                                             new StandardAnalyzer(Version.LUCENE_29));
        HashMap<String, HashSet<String>> map = queryListLucene.makeMap(queryXMLFn);
	HashMap<String, HashSet<String>> map2 = queryListLucene.makeMap(queryXMLFn2);
	HashMap<String, ArrayList<Integer>> nametoNum = new HashMap<String, ArrayList<Integer>>();

	for(String queryName:map.keySet()){

	    String queryStr = "\"" + QueryParser.escape(queryName) + "\"";
	    for(String alias: map.get(queryName)){
		if(!alias.contains(" ")) continue;
		queryStr += " \"" + QueryParser.escape(alias) + "\"^0.01";
	    }
	    Query query = parser.parse(queryStr);
	    TopDocs hits = is.search(query, 500);
	    nametoNum.put(queryName, new ArrayList<Integer>(2));
	    nametoNum.get(queryName).add(new Integer(hits.scoreDocs.length));
	}

	for(String queryName:map2.keySet()){

            String queryStr = "\"" + QueryParser.escape(queryName) + "\"";
            for(String alias: map2.get(queryName)){
                if(!alias.contains(" ")) continue;
                queryStr += " \"" + QueryParser.escape(alias) + "\"^0.01";
            }
            Query query = parser.parse(queryStr);
            TopDocs hits = is.search(query, 500);
            nametoNum.get(queryName).add(1, new Integer(hits.scoreDocs.length));
	    System.out.println(nametoNum.get(queryName).toString());
        }

	for(String name:nametoNum.keySet()){
	    ArrayList l = nametoNum.get(name);
	    if(!l.get(0).equals(l.get(1))){
		System.out.println(name + "  " + l.get(0).toString() + "  " + l.get(1).toString()); 
	    }
	}
    }

    public static HashMap makeMap(String queryXML) throws IOException, FileNotFoundException{
        BufferedReader br = new BufferedReader(new FileReader(queryXML));
        HashMap<String, HashSet<String>> map = new HashMap<String, HashSet<String>>();
        String name = "";
        for (String line; (line = br.readLine()) != null;) {
            if(line.contains("<name>")){
                name = line.split("<name>")[1].split("</name>")[0];
                if(!map.containsKey(name)){
                    map.put(name, new HashSet());
                }
            }
            if(line.contains("<alias>")){
                map.get(name).add(line.split("<alias>")[1].split("</alias>")[0]);
            }
        }
        br.close();

        return map;

    }
}
