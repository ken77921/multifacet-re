
//import indexir.Indexing;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

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

public class lucene {
    public static void main(String[] args) throws IOException, ParseException {
	Directory dir = FSDirectory.open(new File("/iesl/canvas/aimunir/tackbp2016-sf/runs/coldstart2016_pilot_eng_UMass_IESL3.6/index"));
	IndexSearcher is = new IndexSearcher(dir, true);
	QueryParser parser = new QueryParser(Version.LUCENE_29, "contents", 
					 new StandardAnalyzer(Version.LUCENE_29));
	String queryStr = "\"" + QueryParser.escape(args[0]) + "\"";
	//queryStr += " \"" + QueryParser.escape("") + "\"^0.01";
	for(int i = 1; i < args.length; i++){
	     queryStr += " \"" + QueryParser.escape(args[i]) + "\"^0.01";
	}
	Query query = parser.parse(queryStr);
	TopDocs hits = is.search(query, 500);
	for(int i=0; i < hits.scoreDocs.length; i++) {
       	    ScoreDoc scoreDoc = hits.scoreDocs[i];
	    Document luceneDoc = is.doc(scoreDoc.doc);
	    String fn = luceneDoc.get("filename");  
	    System.out.println(hits.scoreDocs[i].toString() + "     " + fn);

	}
	System.out.println(hits.scoreDocs.length);
    }
}