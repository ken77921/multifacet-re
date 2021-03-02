package indexir;
import org.apache.lucene.analysis.ASCIIFoldingFilter;
import org.apache.lucene.analysis.StopFilter;
import org.apache.lucene.analysis.LowerCaseFilter;
import org.apache.lucene.analysis.standard.StandardTokenizer;
import org.apache.lucene.analysis.standard.StandardFilter;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.analysis.StopAnalyzer;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.Tokenizer;
import org.apache.lucene.util.Version;

import java.io.Reader;

import java.util.HashSet;
import java.util.Set;
import java.util.Arrays; 

// Accent insensitive analyzer
public class AccentInsensitiveAnalyzer extends StandardAnalyzer {

    public Version matchVersion;
    public static Set<String> stopWords;
    /*private static final Set<String> DEFAULT_STOP_WORDS = new HashSet<String>(Arrays.asList("an", "and", "are", "as",
					  "at", "be", "but", "by",
					  "for", "if", "in", "into", "is", "it",
					  "no", "not", "of", "on", "or", "such",
					  "that", "the", "their", "then", "there", "these",
					  "they", "this", "to", "was", "will", "with",
					  "de", "la", "que", "el", "en", "los", "del",
					  "se", "las", "por", "un", "para", "con", "una", "su", "al"));*/


    public AccentInsensitiveAnalyzer(Version matchVersion, Set stopWords){
        //super(matchVersion, DEFAULT_STOP_WORDS);
	super(matchVersion, stopWords);
	this.matchVersion = matchVersion;
	this.stopWords = stopWords;
	System.out.println(stopWords.toString());
    }

    @Override
	public TokenStream tokenStream(String fieldName, Reader reader) {
        final Tokenizer source = new StandardTokenizer(matchVersion, reader);

        TokenStream tokenStream = source;
        tokenStream = new StandardFilter(tokenStream);
        tokenStream = new LowerCaseFilter(tokenStream);
        tokenStream = new StopFilter(false, tokenStream, stopWords);
        tokenStream = new ASCIIFoldingFilter(tokenStream);
        return tokenStream;
    }
}