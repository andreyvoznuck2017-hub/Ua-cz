package eu.svoyi.nativeapp;
import java.util.*;
import static eu.svoyi.nativeapp.HomeRules249.*;
public final class HomeRules249Test {
    static int checks;
    static void ok(String name,boolean pass){checks++;if(!pass)throw new AssertionError(name);System.out.println("PASS "+name);}
    static String ids(List<Section> s){List<String> ids=new ArrayList<>();for(Section v:s)ids.add(v.id);return String.join(",",ids);}
    static void throwsArgument(String n,Runnable r){boolean got=false;try{r.run();}catch(IllegalArgumentException e){got=true;}ok(n,got);}
    public static void main(String[] args) {
        List<Section> sections=Arrays.asList(new Section("promo","Реклама","",true),new Section("jobs","Робота","Praha 230 Kč",false),new Section("housing","Житло","Brno 12000 Kč",false),new Section("chat","Чат","community",false));
        ok("server-order-default",ids(ordered(sections,null)).equals("promo,jobs,housing,chat"));
        ok("saved-order",ids(ordered(sections,Arrays.asList("chat","housing","jobs"))).equals("promo,chat,housing,jobs"));
        ok("unknown-stale-duplicates",ids(ordered(sections,Arrays.asList("missing","jobs","jobs","promo","chat"))).equals("promo,jobs,chat,housing"));
        ok("locked-slot-remains",ids(ordered(Arrays.asList(sections.get(1),sections.get(0),sections.get(2)),Arrays.asList("housing"))).equals("housing,promo,jobs"));
        ok("new-server-section-preserved",ordered(sections,Arrays.asList("jobs")).size()==4);
        ok("optional-hidden",!visible(sections.get(1),new HashSet<>(Arrays.asList("jobs")),""));
        ok("promotion-not-hidden",visible(sections.get(0),new HashSet<>(Arrays.asList("promo")),"no match"));
        ok("search-match",visible(sections.get(1),Collections.emptySet(),"praha"));
        ok("search-does-not-unhide",!visible(sections.get(1),new HashSet<>(Arrays.asList("jobs")),"praha"));
        ok("search-miss",!visible(sections.get(1),Collections.emptySet(),"brno"));
        ok("czech-accent-insensitive",matches("České Budějovice", "ceske budejovice"));
        ok("case-whitespace",matches("PRAHA  230 Kč", "  praha 230 "));
        ok("all-search-tokens-required",!matches("Praha 230", "praha 250"));
        ok("ukrainian-query",matches("Робота у ПРАЗІ", "робота празі"));
        ok("unicode-nothing-null",matches(null,null));
        ok("null-does-not-match",!matches(null,"x"));
        ok("not-regex-search",matches("[ДЕМО] житло", "[демо]"));
        ok("normalizer-idempotent",normalize(normalize("České BUDĚJOVICE")).equals(normalize("České BUDĚJOVICE")));
        ok("move-first-up-boundary",encodeOrder(move(sections,null,"jobs",-1)).equals("jobs|housing|chat"));
        ok("move-last-down-boundary",encodeOrder(move(sections,null,"chat",1)).equals("jobs|housing|chat"));
        ok("move-up",encodeOrder(move(sections,null,"chat",-1)).equals("jobs|chat|housing"));
        ok("move-down",encodeOrder(move(sections,null,"jobs",1)).equals("housing|jobs|chat"));
        ok("move-locked-ignored",encodeOrder(move(sections,null,"promo",1)).equals("jobs|housing|chat"));
        ok("preference-decode-dedup",encodeOrder(decodeOrder("jobs|jobs|../../key|housing||chat")).equals("jobs|housing|chat"));
        ok("oversized-preference-rejected",decodeOrder(String.join("",Collections.nCopies(8200,"a"))).isEmpty());
        ok("guest-key-rejected-value",!preferenceKey(1).equals(preferenceKey(2)));
        throwsArgument("guest-cannot-persist",()->preferenceKey(0));
        throwsArgument("negative-account",()->preferenceKey(-1));
        throwsArgument("invalid-id",()->new Section("../s","","",false));
        throwsArgument("duplicate-server-ids",()->ordered(Arrays.asList(sections.get(1),sections.get(1)),null));
        ok("small-screen-one-column",!twoColumns(359,1,true));
        ok("large-font-one-column",!twoColumns(420,1.3f,true));
        ok("normal-grid",twoColumns(380,1,true));
        ok("explicit-list",!twoColumns(800,1,false));
        long now=100000000;
        ok("bookmark-valid",canResume("jobs",now-1000,now,sections,Collections.emptySet()));
        ok("bookmark-expired",!canResume("jobs",now-86400001,now,sections,Collections.emptySet()));
        ok("bookmark-hidden",!canResume("jobs",now-1000,now,sections,new HashSet<>(Arrays.asList("jobs"))));
        ok("bookmark-missing",!canResume("removed",now-1000,now,sections,Collections.emptySet()));
        ok("bookmark-future",!canResume("jobs",now+1,now,sections,Collections.emptySet()));
        ok("locale-cz",locale("cz-CZ").equals("cs"));ok("locale-cs",locale("cs").equals("cs"));ok("locale-en",locale("en-US").equals("en"));ok("locale-uk",locale(null).equals("uk"));
        ok("job-link-normalized",jobRoute("https://test.jkunis.eu/?p=home&view=jobs#job-search").equals("https://test.jkunis.eu/?p=home&native=jobs"));
        ok("relative-job-link",jobRoute("/?p=home&view=jobs&city=Praha").equals("/?city=Praha&p=home&native=jobs"));
        ok("hash-only-job-route",jobRoute("#job-search").equals("/?p=home&native=jobs"));
        for(String u:Arrays.asList("http://test.jkunis.eu/?view=jobs","https://evil.test/?view=jobs","https://test.jkunis.eu.evil.test/?view=jobs","https://evil@test.jkunis.eu/?view=jobs","javascript:alert(1)","https://test.jkunis.eu:8080/?view=jobs","https://test.jkunis.eu/user?view=jobs","/?p=housing&view=jobs","//test.jkunis.eu/?view=jobs","https://test.jkunis.eu/?%broken"))ok("unmodified-untrusted-"+checks,jobRoute(u).equals(u));
        ok("all-other-routes-unmodified",jobRoute("/?p=feed#post-1").equals("/?p=feed#post-1"));
        ok("preserve-repeated-filters",jobRoute("/?view=jobs&city=Praha&city=Brno").equals("/?city=Praha&city=Brno&p=home&native=jobs"));
        ok("null-route",jobRoute(null).equals(""));
        System.out.println("CHECKS_PASSED="+checks);
    }
}
