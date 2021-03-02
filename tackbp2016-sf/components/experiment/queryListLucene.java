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

public class queryListLucene{

    public static void main(String[] args) throws IOException, ParseException {
	String queryXMLFn = args[0];
	String queryName = args[1];
	Directory dir = FSDirectory.open(new File("/iesl/canvas/aimunir/tackbp2016-sf/runs/coldstart2016_pilot_eng_UMass_IESL3.6/index"));
        IndexSearcher is = new IndexSearcher(dir, true);
        QueryParser parser = new QueryParser(Version.LUCENE_29, "contents", 
					     new StandardAnalyzer(Version.LUCENE_29));
	HashMap<String, HashSet<String>> map = queryListLucene.makeMap(queryXMLFn);
	ArrayList<String> list = new ArrayList<String>();
	String queryStr = "\"" + QueryParser.escape(queryName) + "\"";
      	for(String alias: map.get(queryName)){
	    if(!alias.contains(" ")) continue;
	    queryStr += " \"" + QueryParser.escape(alias) + "\"^0.01";
	}
	Query query = parser.parse(queryStr);
	System.out.println(query.toString());
        TopDocs hits = is.search(query, 500);
        for(int i=0; i < hits.scoreDocs.length; i++) {
            ScoreDoc scoreDoc = hits.scoreDocs[i];
            Document luceneDoc = is.doc(scoreDoc.doc);
            String fn = luceneDoc.get("filename");  
            System.out.println(hits.scoreDocs[i].toString() + "     " + fn);

        }
        System.out.println(hits.scoreDocs.length);

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
