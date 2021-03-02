package entity_expansion;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;


public class TopNLinkEntityExpander {
  Map<Integer, Integer> textHashToMaxTargetHash = new HashMap<Integer, Integer>();
  Map<Integer, TopN<String>> targetHashToMaxAnchors = new HashMap<Integer, TopN<String>>();
  
  private static final int MINCOUNT = 5;
  
  private static final Pattern SEPARATOR_PATTERN = Pattern.compile(" ");
  private static final Pattern STOP_WORDS = Pattern.compile("(\\b)(of|the|that|for|an|a|in|de|la|el|en|los|del|las|por|un|para|una|al)(\\s)");
    private static final Pattern CORP_WORDS = Pattern.compile("( llc| l\\.l\\.c\\.|, llc|, l\\.l\\.c\\.| limited| ltd| ltd\\.|, ltd|, ltd\\.| corporation| corp\\.| corp| co\\.| co| incorporated| inc\\.| inc|, incorporated|, inc\\.|, inc| lllp| l\\.l\\.l\\.p\\.|, lllp|, l\\.l\\.l\\.p\\.| llp|, llp| lp| l\\.p\\.|, lp|, l\\.p\\.| pc| p\\.c\\.|, pc|, p\\.c\\.| plc| plc| plc| partners| industries| sa| s\\.a\\.|, sa|, s\\.a\\.|sl| s\\.l\\.|, sl|, s\\.l\\.| slne| s\\.l\\.n\\.e|, slne|, s\\.l\\.n\\.e\\.| sc| s\\.c\\.|, sc|, s\\.c\\.| s\\.cra|, s\\.cra| s de rl| s\\. de r\\.l\\.|, s de rl|, s\\. de r\\.l\\.| s en c| s\\. en c\\.|, s en c|, s\\. en c\\.| y companía| y sucesores)($)");
  


  /**
   * 
   * @param LinkStatisticsFn
   * @param maxN
   * @param requireLinkBack whether the expanded texts have to be linked
   * back to the same article (with maximum probaility) as the query text.
   * @throws IOException
   */
  public TopNLinkEntityExpander(String LinkStatisticsFn, int maxN, 
      boolean requireLinkBack) throws IOException {
    Map<Integer, Integer> textHashToMaxCount = new HashMap<Integer, Integer>();
    
    // First read mapping from text to articles. Then, for reachable articles
    // establish mapping to most frequent anchor text. (Saves memory).
    BufferedReader br = new BufferedReader(new FileReader(LinkStatisticsFn));
    for (String line; (line = br.readLine()) != null;) {
      String[] lineParts = SEPARATOR_PATTERN.split(line, 3);
      if (lineParts.length != 3) {
        continue;
      }
      int count = Integer.parseInt(lineParts[0]);
      if (count < MINCOUNT) {
        continue;
      }
      Integer targetHash = lineParts[1].hashCode();
      String textStripped = CORP_WORDS.matcher(STOP_WORDS.matcher(lineParts[2].toLowerCase()).replaceAll(" ")).replaceAll("");
      int textHash = textStripped.hashCode();
      //int textHash =  lineParts[2].hashCode();
      if (!textHashToMaxCount.containsKey(textHash) ||
          textHashToMaxCount.get(textHash) < count) {
        textHashToMaxTargetHash.put(textHash, targetHash);
        textHashToMaxCount.put(textHash, count);
      }
    }
    br.close();
    br = new BufferedReader(new FileReader(LinkStatisticsFn));
    
    Set<Integer> reachableTargets = 
        new HashSet<Integer>(textHashToMaxTargetHash.values());
    for (String line; (line = br.readLine()) != null;) {
      String[] lineParts = SEPARATOR_PATTERN.split(line, 3);
      if (lineParts.length != 3) {
        continue;
      }
      Integer targetHash = lineParts[1].hashCode();
      if (!reachableTargets.contains(targetHash)) {
        continue;
      }
      int count = Integer.parseInt(lineParts[0]);
      String anchorText =  new String(lineParts[2]);

      String anchorTextStripped = CORP_WORDS.matcher(STOP_WORDS.matcher(lineParts[2].toLowerCase()).replaceAll(" ")).replaceAll("");
      Integer anchorTextHash =  anchorTextStripped.hashCode();

      //      Integer anchorTextHash =  anchorText.hashCode();
      if(requireLinkBack && 
          !targetHash.equals(textHashToMaxTargetHash.get(anchorTextHash))) {
        // Only expansions that are linked back to articles are allowed.
        continue;
      }
      
      if (!targetHashToMaxAnchors.containsKey(targetHash)) {
        targetHashToMaxAnchors.put(targetHash, new TopN<String>(maxN));
      }
      targetHashToMaxAnchors.get(targetHash).add(anchorText, count);
    }
    br.close();
  }
  
  public TopNLinkEntityExpander(String LinkStatisticsFn, int maxN) 
      throws IOException {
    // TODO: change default to true, if it works better.
    this(LinkStatisticsFn, maxN, false);
  }

  public List<String> expand(String text) {
    String textStripped = CORP_WORDS.matcher(STOP_WORDS.matcher(text.toLowerCase()).replaceAll(" ")).replaceAll("");  
    int textHash = textStripped.hashCode(); 
      //int textHash = text.hashCode();
    Integer maxTargetHash;
    if (textHashToMaxTargetHash.containsKey(textHash)) {
      maxTargetHash = textHashToMaxTargetHash.get(textHash);
    } else {
      return new ArrayList<String>();
    }
    if (targetHashToMaxAnchors.containsKey(maxTargetHash)) {
      List<String> retList = 
          targetHashToMaxAnchors.get(maxTargetHash).elementList();
      //retList.remove(text);
      return retList;
    } else {
      return new ArrayList<String>();
    }
  }

}
