package entity_expansion;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import java.lang.Double;

public class TopNAliasExpander{


  Map<String, TopN<String>> targetPageToTopRedirects_EN = new HashMap<String, TopN<String>>();
  Map<String, TopN<String>> targetPageToTopRedirects_SP = new HashMap<String, TopN<String>>();
  Map<String, TopN<String>> redirectToPage_EN = new HashMap<String, TopN<String>>();
  Map<String, TopN<String>> redirectToPage_SP = new HashMap<String, TopN<String>>();
  Map<String, String> engTospa = new HashMap<String, String>();
  Map<String, String> spaToeng = new HashMap<String, String>();

  private static final double MINCOUNT = 0.10;
  private static final Pattern SEPARATOR_PATTERN = Pattern.compile("\t");
  private static final Pattern STOP_WORDS_SP = Pattern.compile("(\\b)(of|the|that|for|an|a|in|de|la|el|en|los|del|las|por|un|para|una|al)(\\s)");
  //private static final Pattern STOP_WORDS_SP = Pattern.compile("(\\b)(de|la|el|en|los|del|las|por|un|para|una|al)(\\s)");
  private static final Pattern STOP_WORDS_EN = Pattern.compile("(\\b)(of|the|that|for|an|a|in)(\\s)");
  private static final Pattern CORP_WORDS = Pattern.compile("( llc| l\\.l\\.c\\.|, llc|, l\\.l\\.c\\.| limited| ltd| ltd\\.|, ltd|, ltd\\.| corporation| corp\\.| corp| co\\.| co| incorporated| inc\\.| inc|, incorporated|, inc\\.|, inc| lllp| l\\.l\\.l\\.p\\.|, lllp|, l\\.l\\.l\\.p\\.| llp|, llp| lp| l\\.p\\.|, lp|, l\\.p\\.| pc| p\\.c\\.|, pc|, p\\.c\\.| plc| plc| plc| partners| industries| sa| s\\.a\\.|, sa|, s\\.a\\.|sl| s\\.l\\.|, sl|, s\\.l\\.| slne| s\\.l\\.n\\.e|, slne|, s\\.l\\.n\\.e\\.| sc| s\\.c\\.|, sc|, s\\.c\\.| s\\.cra|, s\\.cra| s de rl| s\\. de r\\.l\\.|, s de rl|, s\\. de r\\.l\\.| s en c| s\\. en c\\.|, s en c|, s\\. en c\\.| y companía| y sucesores)($)");

    /**                                                                                                                                                                             
     *                                                                                                                                                                             
     * @param RedirectFN                                                                                                                                                            
     * @param maxN                                                                                                                                                                  
     * @throws IOException                                                                                                                                                      
    */

    public TopNAliasExpander(String LinkBackFN_EN, String LinkBackFN_SP, String AliasFN_EN, String AliasFN_SP,
				String LangLinkFN, boolean requireLinkBack, int maxN) throws IOException {

	//build maps for spanish and enlgish redirects with top scores
	getExpansionMap(LinkBackFN_EN, AliasFN_EN, requireLinkBack, maxN, STOP_WORDS_EN, targetPageToTopRedirects_EN, redirectToPage_EN);
	getExpansionMap(LinkBackFN_SP, AliasFN_SP, requireLinkBack, maxN, STOP_WORDS_SP, targetPageToTopRedirects_SP, redirectToPage_SP);
	
	//build map for links between spanish articles and english articles
	BufferedReader br = new BufferedReader(new FileReader(LangLinkFN));                                                                                                        
	for (String line; (line = br.readLine()) != null;) {                                                                                                                        
	    String[] lineParts = SEPARATOR_PATTERN.split(line, 2);                                                                                                                  
	    String spanishPage = lineParts[0].substring(7, lineParts[0].length()-7).replace("_", " ");                                                                              
	    String englishPage = lineParts[1].substring(7,lineParts[1].length()-7).replace("_", " ");                                                                               
   	    Integer englishHash = englishPage.hashCode();                                                                                                                           
	    Integer spanishHash = spanishPage.hashCode();                                                                                                                           
	    if(!engTospa.containsKey(englishPage)){                                                                                                                          
		engTospa.put(englishPage, spanishPage);                                                                                                               
		spaToeng.put(spanishPage, englishPage);
	    }                                                                                                                                                                      
      	}                                                                                                                                                                          
	br.close();         

    }

    public void  getExpansionMap(String LinkBackFn, String AliasFn, boolean requireLinkBack, int maxN, Pattern stopWords,
				 Map<String, TopN<String>> targetPageToTopRedirects, Map<String, TopN<String>> redirectToPage) throws IOException{
	//map used for link back check(only uses aliases that refer back to article with highest prob)
	Map<String, TopN<String>> aliasToTopAnchor = new HashMap<String, TopN<String>>();
	
	BufferedReader br = new BufferedReader(new FileReader(LinkBackFn));
	for (String line; (line = br.readLine()) != null;) {
	    String[] lineParts = SEPARATOR_PATTERN.split(line, 3);
	    String rawAlias = lineParts[0].substring(7, lineParts[0].length()-7).replace("_", " ").toLowerCase();
	    String alias = CORP_WORDS.matcher(stopWords.matcher(rawAlias).replaceAll("")).replaceAll("");
	    String anchor = lineParts[1].substring(7,lineParts[1].length()-7).replace("_", " ");
	    double score = Double.parseDouble(lineParts[2]);
	    //Integer aliasHash = alias.hashCode();
	    //Integer anchorHash = anchor.hashCode();
	    if(!redirectToPage.containsKey(alias)){
		redirectToPage.put(alias, new TopN<String>(1));
	    }
	    redirectToPage.get(alias).add(anchor, score);
	}
	br.close();


	br = new BufferedReader(new FileReader(AliasFn));
	for (String line; (line = br.readLine()) != null;) {
	    String[] lineParts = SEPARATOR_PATTERN.split(line, 3);
            String redirect = lineParts[0].substring(7, lineParts[0].length()-7).replace("_", " ");
            String page = lineParts[1].substring(7,lineParts[1].length()-7).replace("_", " ");
            double count = Double.parseDouble(lineParts[2]);
            //Integer redirectHash = redirect.hashCode();
            //Integer pageHash = page.hashCode();
	
	    if(count < MINCOUNT){
                continue;
            }

	    if(!targetPageToTopRedirects.containsKey(page)){
		targetPageToTopRedirects.put(page, new TopN<String>(maxN));
		targetPageToTopRedirects.get(page).add(page, 1.0);
	    }
  
	    if(!requireLinkBack){
		targetPageToTopRedirects.get(page).add(redirect, count);
	    } else {
		List<String> currExpansions = redirectToPage.get(CORP_WORDS.matcher(stopWords.matcher(redirect.toLowerCase()).replaceAll("")).replaceAll("")).elementList();
		if(currExpansions.size() > 0 && currExpansions.get(0).equals(page)){
		    targetPageToTopRedirects.get(page).add(redirect, count);
		}
	    }
	}
	br.close();
  }


  public List<String> expand(String name) {
      String text_en = CORP_WORDS.matcher(STOP_WORDS_EN.matcher(name.toLowerCase()).replaceAll("")).replaceAll("");
      //int textHash = text.hashCode();                                                                                                
      Set<String> expansions = new HashSet<String>();
      if(redirectToPage_EN.containsKey(text_en)){                                                                                                                                  
	  String pageEN = redirectToPage_EN.get(text_en).elementList().get(0);                                                                                                    
	  if(targetPageToTopRedirects_EN.containsKey(pageEN)){
	      expansions.addAll(targetPageToTopRedirects_EN.get(pageEN).elementList());                                                                                             
	  }
	  //add the redirects for corresponding spanish article
   	  if(engTospa.containsKey(pageEN)){
	      String pageSP = engTospa.get(pageEN);
	      if(targetPageToTopRedirects_SP.containsKey(pageSP)){
		  expansions.addAll(targetPageToTopRedirects_SP.get(pageSP).elementList());
	      }
	  }
      }
      //perform same operation for spanish to english
      String text_sp = CORP_WORDS.matcher(STOP_WORDS_SP.matcher(name.toLowerCase()).replaceAll("")).replaceAll("");
      if(redirectToPage_SP.containsKey(text_sp)){
	  String pageSP = redirectToPage_SP.get(text_sp).elementList().get(0);
	  if(targetPageToTopRedirects_SP.containsKey(pageSP)){
	      expansions.addAll(targetPageToTopRedirects_SP.get(pageSP).elementList());
     	  }
	  if(spaToeng.containsKey(pageSP)){
	      String pageEN = spaToeng.get(pageSP);
	      if(targetPageToTopRedirects_EN.containsKey(pageEN)){
		  expansions.addAll(targetPageToTopRedirects_EN.get(pageEN).elementList());
	      }
	  }
      }
      return new ArrayList<String>(expansions);
  }


}
