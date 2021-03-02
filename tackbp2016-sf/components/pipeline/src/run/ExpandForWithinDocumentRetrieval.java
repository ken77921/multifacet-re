package run;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import query.QueryList;


public class ExpandForWithinDocumentRetrieval {
    /**
     * Expands a query.xml:
     * 1) aliases are added
     * 2) relations are listet explicitly
     *
     * @param args
     * @throws IOException
     */
    public static void main(String[] args) throws IOException {
        if (args.length != 12 && args.length != 13) {
            System.out.println("Expand <query_xml> <relations> <relation_config> <expansions> <maxN> <org_suffixes> <expanded.xml> [<require_backlinks=true|false|none|wiki|rules|suffix|lastname>]");
            System.out.println("for 'require_backlinks', 'true' means precision expansion, 'false' means standard expansion, 'none' means no expansion");
            System.out.println(" 'wiki' means only wiki expansion with backlinks (no rules), 'rules' means only rule-based (org: suffixes, per: last name).");
            System.out.println(" 'suffix' means only org: suffixes, 'lastname' for only per: last name.");
            System.out.println(" 'redirect_en' and 'redirect_sp' means the scored redirect files for wikipedia redirect pages");
            System.out.println(" 'linkback_en' and 'linkback_sp' means the alias files for only using aliases that most likely link back to the page");
            System.out.println(" 'langLinkFn' means the mapping from english wiki article titles to the corresponding spanish wiki titles");
            return;
        }
        String qXmlFn = args[0];
        String relsFn = args[1];
        String relsCfgFn = args[2];
        String expansionStatFn = args[3];
        String redirectStatFn_EN = args[4];
        String redirectStatFn_SP = args[5];
        String linkBackFn_EN = args[6];
        String linkBackFn_SP = args[7];
        String langLinkFn = args[8];
        int maxN = Integer.parseInt(args[9]);
        String orgSuffixFn = args[10];
        String outFn = args[11];

        // Do expansion unless explicitely not.
        boolean doExpansion = args.length < 12 || !"none".equals(args[12]);

        // Default is precision oriented expansion.
        boolean requireLinkBack = args.length > 12 ? Boolean.parseBoolean(args[12])
                : true; // TODO: change default if profitable.

        List<String> orgSuffixes = new ArrayList<String>();

        BufferedReader br = new BufferedReader(new FileReader(orgSuffixFn));
        for (String suffix; (suffix = br.readLine()) != null;) {
            orgSuffixes.add(suffix);
        }
        br.close();

        QueryList ql = new QueryList(qXmlFn);
        ql.expandRelations(relsFn, relsCfgFn);
        boolean lowercase = true;
        boolean uppercase = true;
        boolean camelcase = true;
        ql.addWithinDocumentExpansions(expansionStatFn, redirectStatFn_EN, redirectStatFn_SP, linkBackFn_EN, linkBackFn_SP, langLinkFn, maxN, false, requireLinkBack, orgSuffixes,lowercase,uppercase,camelcase);

        BufferedWriter bw = new BufferedWriter(new FileWriter(outFn));
        ql.writeTo(bw);
        bw.close();
    }
}
