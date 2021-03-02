package query;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.IOException;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.Iterator;
import java.util.regex.Pattern;
import java.lang.Character;

import javax.xml.parsers.ParserConfigurationException;
import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;

import org.apache.commons.lang3.StringEscapeUtils;
import org.apache.log4j.Logger;
import org.xml.sax.Attributes;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;
import org.xml.sax.helpers.DefaultHandler;

import com.google.common.collect.HashMultimap;
import com.google.common.collect.Multimap;

import entity_expansion.TopNLinkEntityExpander;
import entity_expansion.TopNAliasExpander;

public class QueryList {
  static Logger logger = Logger.getLogger(QueryList.class.getName());

  /*
  <query id="SF515">
    <name>German ARD</name>
    <docid>XIN_ENG_20080726.0002.LDC2009T13</docid>
    <enttype>ORG</enttype>
    <nodeid>E0623403</nodeid>
    <ignore>org:country_of_headquarters org:date_founded  org:website</ignore>
  </query>
  */
  public class QueryListReader extends DefaultHandler {

    private StringBuffer buffer;
    private Query query;
    private QueryList ql;
    private Attributes attributes;

    public QueryListReader(QueryList ql) {
      this.ql = ql;
    }

    @Override
    public void characters(char[] ch, int start, int length)
        throws SAXException {
      this.buffer.append(Arrays.copyOfRange(ch, start, start + length));
    }

    @Override
    public void endElement(String uri, String localName, String qName)
        throws SAXException {
      if (query == null) {
        return;
      }
      if (localName.equalsIgnoreCase("query")) {
        if (query.id == null || query.id.isEmpty() || query.name == null ||
            query.name.isEmpty() || query.enttype == null ||
            query.enttype.isEmpty()) {
          logger.warn("Found query lacking important information: " + query);
        }
        ql.addNewQuery(query);
        query = null;
      } else if (localName.equalsIgnoreCase("name")) {
        query.name = buffer.toString();
      } else if (localName.equalsIgnoreCase("enttype")) {
        query.enttype = buffer.toString();
      } else if (localName.equalsIgnoreCase("ignore")) {
        for (String ig : buffer.toString().split("\\s+")) {
          query.ignore.add(ig);
        }
      } else if (localName.equalsIgnoreCase("ignore_slotfiller")) {
        query.ignoreSlotfillers.put(attributes.getValue("rel"),
            buffer.toString());
      } else if (localName.equalsIgnoreCase("alias")) {
        query.aliases.add(buffer.toString());
      } else if (localName.equalsIgnoreCase("docid")) {
        query.docId = buffer.toString();
      } else if (localName.equalsIgnoreCase("nodeid")) {
        query.nodeId = buffer.toString();
      } else if (localName.equalsIgnoreCase("beg")) {
        query.beg = buffer.toString();
      } else if (localName.equalsIgnoreCase("end")) {
        query.end = buffer.toString();
      } else if (localName.equalsIgnoreCase("slot")) { // for coldstart
        query.slot = buffer.toString();
      } else if (localName.equalsIgnoreCase("rel")) {
        if (attributes.getValue("listtype").equalsIgnoreCase("true")) {
          logger.debug("Found new listtype relation");
          query.listRelations.add(buffer.toString());
        } else {
          logger.debug("Found new single relation");
          query.singleRelations.add(buffer.toString());
        }
      } else {
        if (query != null) {
          logger.warn("Encountered unhandled element in Query: " + localName);
        }
      }
    }

    @Override
    public void startElement(String uri, String localName, String qName,
        Attributes atts) throws SAXException {
      if (localName.equalsIgnoreCase("query")) {
        if (atts.getValue("id") == null) {
          logger.error("Query without ID field (required)! Skipping.");
          query = null;
          return;
        }
        query = new Query();
        query.id = atts.getValue("id");
        logger.debug("New query found, " + query);
      }
      attributes = atts;
      buffer = new StringBuffer();
    }

    @Override
    public void warning(SAXParseException e) throws SAXException {
      logger.warn(e.getMessage());
    }

    @Override
    public void error(SAXParseException e) throws SAXException {
      logger.error(e.getMessage());
    }

    @Override
    public void fatalError(SAXParseException e) throws SAXException {
      logger.error(e.getMessage());
    }

  }

  public class Query {
    private String end = "";
    private String beg = "";
    private String nodeId = "";
    private String docId = "";
    private String id = "";
    private String name = "";
    private String slot = ""; // for coldstart
    private String enttype = "";
    private List<String> ignore = new ArrayList<String>();
    private List<String> aliases = new ArrayList<String>();
    private List<String> listRelations = new ArrayList<String>();
    private List<String> singleRelations = new ArrayList<String>();
    private Multimap<String, String> ignoreSlotfillers = HashMultimap.create();

    public Query(String id, String name, String enttype) {
      this.id = id;
      this.name = name;
      this.enttype = enttype;
    }

    public Query() {
    }

    public void writeTo(BufferedWriter bw) throws IOException {
      bw.append("<query id=\"" + StringEscapeUtils.escapeXml(id) + "\">\n");
      bw.append(" <name>" + StringEscapeUtils.escapeXml(name) + "</name>\n");
      bw.append(" <docid>" + StringEscapeUtils.escapeXml(docId) + "</docid>\n");
      bw.append(" <beg>" + StringEscapeUtils.escapeXml(beg) + "</beg>\n");
      bw.append(" <end>" + StringEscapeUtils.escapeXml(end) + "</end>\n");
      bw.append(" <enttype>" + StringEscapeUtils.escapeXml(enttype) + "</enttype>\n");
      if (!nodeId.isEmpty()) {
        bw.append(" <nodeid>" + StringEscapeUtils.escapeXml(nodeId) + "</nodeid>\n");
      }
      if (!ignore.isEmpty()) {
        bw.append(" <ignore>");
        String sep = "";
        for (String ig : ignore) {
          bw.append(sep); sep = " ";
          bw.append(StringEscapeUtils.escapeXml(ig));
        }
        bw.append("</ignore>\n");
      }
      for (String al : aliases) {
        bw.append(" <alias>" + StringEscapeUtils.escapeXml(al) + "</alias>\n");
      }
      for (String lrel : listRelations) {
        bw.append(" <rel listtype=\"true\">" + StringEscapeUtils.escapeXml(lrel) + "</rel>\n");
      }
      for (String srel : singleRelations) {
        bw.append(" <rel listtype=\"false\">" + StringEscapeUtils.escapeXml(srel) + "</rel>\n");
      }
      for (String rel : ignoreSlotfillers.keySet()) {
        for (String slotfiller : ignoreSlotfillers.get(rel)) {
          bw.append(" <ignore_slotfiller rel=\"");
          bw.append(StringEscapeUtils.escapeXml(rel));
          bw.append("\">");
          bw.append(StringEscapeUtils.escapeXml(slotfiller));
          bw.append("</ignore_slotfiller>\n");
        }
      }
      bw.append("</query>\n");
    }

    public String getName() {
      return name;
    }

    public List<String> getAliases() {
      return aliases;
    }

    public String getEnttype() {
      return enttype;
    }

    public String getId() {
      return id;
    }

    public Multimap<String, String> getIgnoreSlotfillers() {
      return ignoreSlotfillers;
    }

    public List<String> getIgnore() {
      return ignore;
    }

    public List<String> getRelations() {
      List<String> rels =
          new ArrayList<String>(singleRelations.size() + listRelations.size());
      rels.addAll(singleRelations);
      rels.addAll(listRelations);
      return rels;
    }

    public List<String> getSingleRelations() {
      return singleRelations;
    }

    public List<String> getListRelations() {
      return listRelations;
    }

    public String toString() {
      return "Query id=" + id + ", enttype=" + enttype + ", name=" + name;
    }

    public String getNodeId() {
      return nodeId;
    }

    public String getDocId() {
      return docId;
    }

    public String getBeg() {
      return beg;
    }

    public String getEnd() {
      return end;
    }
  }

  Map<String, Query> idToQuery = new TreeMap<String, QueryList.Query>();

  /**
   * Reads a simple or expanded query list from xml file.
   * @param qXmlFn
   */
  public QueryList(String qXmlFn) {
    readFromXML(qXmlFn);
  }

  public boolean hasQueryId(String qid) {
    return null != qid && idToQuery.containsKey(qid);
  }

  public Query getQueryById(String qid) {
    if (!hasQueryId(qid)) {
      throw new IllegalArgumentException("Unknown query id: " + qid);
    }
    return idToQuery.get(qid);
  }

  public QueryList() {
  }

  // TODO(tbarth): Static factory method instead
  private void readFromXML(String qXmlFn) {
    try {
      SAXParserFactory factory = SAXParserFactory.newInstance();
      factory.setNamespaceAware(true);
      //factory.setValidating(true);
      // Comment in if we can expect to actually find a DTD defintion in XML
      // file.
      SAXParser parser = factory.newSAXParser();
      parser.parse(qXmlFn, new QueryListReader(this));
    } catch(SAXException e) {
      logger.error("Problem reading query XML file: " + e.toString());
    } catch(IOException e) {
      logger.error("Problem reading query file: " + e.toString());
    } catch (ParserConfigurationException e) {
      // TODO Auto-generated catch block
      e.printStackTrace();
    }
  }

  public void expandRelations(String relsFn, String relsCfgFn)
      throws IOException {
    Map<String, String> relToEnttype = new HashMap<String, String>();
    Set<String> listRels = new HashSet<String>();
    BufferedReader br = new BufferedReader(new FileReader(relsCfgFn));
    for (String line; (line = br.readLine()) != null;) {
      line = line.trim();
      String[] parts = line.split("\\s+", 3);
      if (parts.length == 3) {
        String rel = parts[0];
        String prop = parts[1];
        String val = parts[2];
        if (prop.equals("enttype")) {
          relToEnttype.put(rel, val);
        } else if (prop.equals("listtype") && val.equals("true")) {
          listRels.add(rel);
        }
      }
    }
    br.close();

    br = new BufferedReader(new FileReader(relsFn));
    for (String line; (line = br.readLine()) != null;) {
      String rel = line.trim();
      String enttype = relToEnttype.get(rel);
      for (Query q : getQueries()) {
        if (q.slot.equals(rel) || // For coldstart
            (q.slot.isEmpty() && q.enttype.equals(enttype) && !q.ignore.contains(rel))) {
          if (listRels.contains(rel)) {
            q.listRelations.add(rel);
          } else {
            q.singleRelations.add(rel);
          }
        }

      }
    }
    br.close();
  }

  public static String removeAccents(String s) {
    return Normalizer.normalize(s, Normalizer.Form.NFKD).replaceAll("[^\\p{ASCII}]", "");
  }

  public static String removePunctuation(String s, String rpl) {
    return s.replaceAll("\\p{Punct}",rpl);
  }

  public static String removePunctuationExceptDash(String s, String rpl) {
    return s.replaceAll("(?!-)\\p{Punct}", rpl);
  }

  public static String replaceDoubleSpace(String s) {
    return s.replaceAll("\\s[\\s]*", " ");
  }

  //public static String toCamelCase(String s) {
  //  if (s.contains(" ")) {
  ////    System.out.print(s);
  //    String[] splt = s.split(" ");
  //    StringBuilder res = new StringBuilder();
  //    for (String p: splt) {
  //      res.append(p.substring(0,1).toUpperCase());
  //      if (p.length() > 1)
  //        res.append(p.substring(1));;
  //    }
  //    return res.toString();
  //  } else {
  //    return s;
  //  }
  //}
  public static String toCamelCase(String s) {
    if (s.contains(" ")) {
      String[] splt = s.split(" ");
      StringBuilder res = new StringBuilder();
      for (String p: splt) {
        if (p.length() > 0) {
          res.append(p.substring(0,1).toUpperCase());
          if (p.length() > 1) {
            res.append(p.substring(1));
          }
        }
      }
      return res.toString();
    } else {
      return s;
    }
  }


  public static Set<String> filterAliases(Set<String> aliases) {
    Iterator<String> iter = aliases.iterator();
    while(iter.hasNext()) {
      String a = iter.next();
      if (a.length() <= 1)
        iter.remove();
      else if (ALIAS_STOPWORDS.contains(a.toLowerCase()))
        iter.remove();
    }
    return aliases;
  }

  public static void relaxForWithinDocumentMatch(Query q, boolean lowercase,boolean uppercase,boolean camelcase) {
    Set<String> exp = new HashSet<>();
    for (String a: q.aliases) {

      // The string itself
      exp.add(replaceDoubleSpace(a));

      // Remove accents
      String noAccents = removeAccents(a);
      exp.add(replaceDoubleSpace(noAccents));

      // Remove punct
      String noPunct = removePunctuation(a,"");
      exp.add(replaceDoubleSpace(noPunct));

      // Remove punct w/o dash
      String noPunctExceptDash = removePunctuationExceptDash(a,"");
      exp.add(replaceDoubleSpace(noPunctExceptDash));

      // Remove punct, Remove accents
      String noPunctNoAccent = removePunctuation(removeAccents(a),"");
      exp.add(replaceDoubleSpace(noPunctNoAccent));

      // Remove punct w/o dash, Remove accents
      String noPunctExceptDashNoAccent = removePunctuationExceptDash(removeAccents(a),"");
      exp.add(replaceDoubleSpace(noPunctExceptDashNoAccent));

      // Replace punct with space
      String replPunct = removePunctuation(a," ");
      exp.add(replaceDoubleSpace(replPunct));

      // Replace punct w/o dash
      String replPunctExceptDash = removePunctuationExceptDash(a," ");
      exp.add(replaceDoubleSpace(replPunctExceptDash));

      // Replace punct, Remove accents
      String replPunctNoAccent = removePunctuation(removeAccents(a)," ");
      exp.add(replaceDoubleSpace(replPunctNoAccent));

      // Replace punct w/o dash, Remove accents
      String replPunctExceptDashNoAccent = removePunctuationExceptDash(removeAccents(a)," ");
      exp.add(replaceDoubleSpace(replPunctExceptDashNoAccent));

    }
    Set<String> lc_exp = new HashSet<>();
    if (lowercase) {
      for (String e : exp)
        lc_exp.add(e.toLowerCase());
      exp.addAll(lc_exp);
      lc_exp.clear();
    }

    Set<String> uc_exp = new HashSet<>();
    if (uppercase) {
      for (String e : exp)
        uc_exp.add(e.toUpperCase());
      exp.addAll(uc_exp);
      uc_exp.clear();
    }

    Set<String> cc_exp = new HashSet<>();
    if (camelcase) {
      for (String e : exp)
        cc_exp.add(toCamelCase(e));
      exp.addAll(cc_exp);
      cc_exp.clear();
    }
    
    exp = filterAliases(exp);
    q.aliases.clear();
    q.aliases.addAll(exp);

  }


  public void addWithinDocumentRuleExpansions(Collection<String> orgSuffixes,boolean lowercase,boolean uppercase,boolean camelcase) throws IOException {
    for (Query q : getQueries()) {
      if ("per".equals(q.enttype.toLowerCase())) {
        String[] parts = q.name.split(" ");
        for (String namePart: parts) {
          if (!q.aliases.contains(namePart))
            q.aliases.add(namePart);
        }
      }
      if ("org".equals(q.enttype.toLowerCase())) {
        for (String expansion : suffixExpand(q.name, orgSuffixes)) {
          if (!expansion.equals(q.name) && !expansion.isEmpty() &&
                  Character.isUpperCase(expansion.charAt(0)) &&
                  !q.aliases.contains(expansion)) { // TODO: this is quadratic.
            q.aliases.add(expansion);
          }
        }
      }
      relaxForWithinDocumentMatch(q,lowercase,uppercase,camelcase);
    }
  }



  public void addRuleExpansions(boolean addLastName, Collection<String> orgSuffixes)
      throws IOException {
    for (Query q : getQueries()) {
      if ("per".equals(q.enttype.toLowerCase())) {
	String[] parts = q.name.split(" ");
	String lastName = parts[parts.length - 1];
	ArrayList<String> aliasesToAdd = new ArrayList<String>();
	if(addLastName){
	    aliasesToAdd.add(lastName);
	}
	if(parts.length == 3){
	    String firstMiddle = parts[0] + " " + parts[1];
	    String firstLast = parts[0] + " " + parts[2];
	    String firstInitialLast = parts[0] + " " +  Character.toUpperCase(parts[1].charAt(0)) + ". " + parts[2];
	    aliasesToAdd.add(firstMiddle);
	    aliasesToAdd.add(firstLast);
	    aliasesToAdd.add(firstInitialLast);
	}
	else if(parts.length > 3){
	    String firstMiddle = parts[0] + " " + parts[1];
	    String firstLastPrimary = parts[0] + " " + parts[parts.length - 2];
	    String firstLastSecondary = parts[0] + " " + parts[parts.length -1];
	    String firstInitialLastPrimary = parts[0] + " " + Character.toUpperCase(parts[1].charAt(0)) + ". " + parts[parts.length - 2];
	    String firstInitialLastSecondary = parts[0] + " " + Character.toUpperCase(parts[1].charAt(0)) + ". " + parts[parts.length -1];
	    aliasesToAdd.add(firstMiddle);
	    aliasesToAdd.add(firstLastPrimary);
	    aliasesToAdd.add(firstLastSecondary);
	    aliasesToAdd.add(firstInitialLastPrimary);
	    aliasesToAdd.add(firstInitialLastSecondary);
	}
	for(String expansion:aliasesToAdd){
	    if(!q.aliases.contains(expansion)){
		//remove noisy expansions of the form (T. Miller)
		if(expansion.split("\\.").length == 2 && expansion.split("\\.")[0].length() == 1){
		    continue;
		}
		q.aliases.add(expansion);
	    }
	}
      }
      if ("org".equals(q.enttype.toLowerCase())) {
        for (String expansion : suffixExpand(q.name, orgSuffixes)) {
          if (!expansion.equals(q.name) && !expansion.isEmpty() &&
              Character.isUpperCase(expansion.charAt(0)) &&
              !q.aliases.contains(expansion)) { // TODO: this is quadratic.
            q.aliases.add(expansion);
          }
        }
	Pattern CORP_WORDS = Pattern.compile("( llc| l\\.l\\.c\\.|, llc|, l\\.l\\.c\\.| limited| ltd| ltd\\.|, ltd|, ltd\\.| corporation| corp\\.| corp| co\\.| co| incorporated| inc\\.| inc|, incorporated|, inc\\.|, inc| lllp| l\\.l\\.l\\.p\\.|, lllp|, l\\.l\\.l\\.p\\.| llp|, llp| lp| l\\.p\\.|, lp|, l\\.p\\.| pc| p\\.c\\.|, pc|, p\\.c\\.| plc| plc| plc| partners| industries| sa| s\\.a\\.|, sa|, s\\.a\\.|sl| s\\.l\\.|, sl|, s\\.l\\.| slne| s\\.l\\.n\\.e|, slne|, s\\.l\\.n\\.e\\.| sc| s\\.c\\.|, sc|, s\\.c\\.| s\\.cra|, s\\.cra| s de rl| s\\. de r\\.l\\.|, s de rl|, s\\. de r\\.l\\.| s en c| s\\. en c\\.|, s en c|, s\\. en c\\.| y companía| y sucesores)($)");
	String org = CORP_WORDS.matcher(q.name).replaceAll("");
	if(!org.equals(q.name) && !org.isEmpty() && !q.aliases.contains(org)){
	    q.aliases.add(org);
	}
      }
    }
  }

  public void addWikiExpansions(String expansionStatFn, int maxN,
      boolean requireLinkBack)
      throws IOException {
    TopNLinkEntityExpander expander =
        new TopNLinkEntityExpander(expansionStatFn, maxN, requireLinkBack);
    for (Query q : getQueries()) {
      for (String expansion : expander.expand(q.name)) {
        if (!expansion.equals(q.name) && !expansion.isEmpty() &&
            Character.isUpperCase(expansion.charAt(0)) &&
            !q.aliases.contains(expansion)) { // TODO: this is quadratic.
          q.aliases.add(expansion);
        }
      }
    }
  }

  

    public void addAliasExpansions(String linkBackFn_EN,
				   String linkBackFn_SP, String redirectFn_EN, String redirectFn_SP, String langLinkFn, boolean requireLinkBack, int maxN) throws IOException{
        TopNAliasExpander expander = new TopNAliasExpander(linkBackFn_EN, linkBackFn_SP, redirectFn_EN, redirectFn_SP, langLinkFn, requireLinkBack, maxN);
	for (Query q : getQueries()) {
	    for (String expansion : expander.expand(q.name)) {
		if (!expansion.equals(q.name) && !expansion.isEmpty() &&
		    Character.isUpperCase(expansion.charAt(0)) &&
		    !q.aliases.contains(expansion) && expansion.length() < 150) { // TODO: this is quadratic.                                                                       
		    q.aliases.add(expansion);
		}
	    }
	}

    }

 
    public void addExpansions(String expansionStatFn, String redirectFn_EN, String redirectFn_SP,
			      String linkBackFn_EN, String linkBackFn_SP, String langLinkFn, int maxN,
			      boolean addLastName, boolean requireLinkBack, Collection<String> orgSuffixes) throws IOException {
    addAliasExpansions(linkBackFn_EN, linkBackFn_SP, redirectFn_EN, redirectFn_SP, langLinkFn, requireLinkBack, maxN);
    addWikiExpansions(expansionStatFn, maxN, requireLinkBack);
    addRuleExpansions(addLastName, orgSuffixes);
  }

  public void addWithinDocumentExpansions(String expansionStatFn, String redirectFn_EN, String redirectFn_SP,
                            String linkBackFn_EN, String linkBackFn_SP, String langLinkFn, int maxN,
                            boolean addLastName, boolean requireLinkBack, Collection<String> orgSuffixes,boolean lowercase,boolean uppercase,boolean camelcase) throws IOException {
    addWikiExpansions(expansionStatFn, maxN, requireLinkBack);
    addAliasExpansions(linkBackFn_EN, linkBackFn_SP, redirectFn_EN, redirectFn_SP, langLinkFn, requireLinkBack, maxN);
    addRuleExpansions(addLastName, orgSuffixes);
    addWithinDocumentRuleExpansions(orgSuffixes,lowercase,uppercase,camelcase);
  }

  private Collection<String> suffixExpand(String name, Collection<String> orgSuffixes) {
    List<String> alternateNames = new ArrayList<String>();
    String baseForm = name;
    // base form is shortest stripped off suffix form.
    for (String suffix : orgSuffixes) {
      if (name.endsWith(suffix) &&
          baseForm.length() > (name.length() - suffix.length())) {
        baseForm = name.substring(0, name.length() - suffix.length());
      }
    }
    if (baseForm.isEmpty()) {
      return alternateNames;
    }
    if (!baseForm.equals(name)) {
      alternateNames.add(baseForm);
    }
    for (String suffix : orgSuffixes) {
      String alternateName = baseForm + suffix;
      if (!alternateName.equals(name)) {
        alternateNames.add(alternateName);
      }
    }
    return alternateNames;
  }

  public Collection<Query> getQueries() {
    return idToQuery.values();
  }

  public void writeTo(BufferedWriter bw) throws IOException {
    bw.append("<?xml version='1.0' encoding='UTF-8'?>\n<kbpslotfill>\n");
    for (Query q : getQueries()) {
      q.writeTo(bw);
    }
    bw.append("</kbpslotfill>\n");
  }

  public Query addNewQuery(String id, String name, String entType) {
    Query q = new Query(id, name, entType);
    this.idToQuery.put(q.getId(), q);
    return q;
  }

  public Query addNewQuery(Query q) {
    this.idToQuery.put(q.getId(), q);
    return q;
  }



  private static final Set<String> ALIAS_STOPWORDS = new HashSet<String>(Arrays.asList("an", "and", "are", "as",
          "at", "be", "but", "by",
          "for", "if", "in", "into", "is", "it",
          "no", "not", "of", "on", "or", "such",
          "that", "the", "their", "then", "there", "these",
          "they", "this", "to", "was", "will", "with",
          "de", "la", "que", "el", "en", "los", "del",
          "se", "las", "por", "un", "para", "con", "una", "su", "al"));


}
