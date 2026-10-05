package eu.svoyi.nativeapp;

import java.net.URI;
import java.net.URISyntaxException;
import java.net.URLDecoder;
import java.text.Normalizer;
import java.util.*;

/** Pure home-only rules; stores presentation preferences, never server records or credentials. */
public final class HomeRules249 {
    private HomeRules249() {}
    public static final class Section {
        public final String id, title, searchText;
        public final boolean locked;
        public Section(String id, String title, String searchText, boolean locked) {
            if (id == null || !id.matches("[a-z0-9_-]{1,64}")) throw new IllegalArgumentException("section id");
            this.id = id; this.title = title == null ? "" : title;
            this.searchText = searchText == null ? "" : searchText; this.locked = locked;
        }
    }
    public static String normalize(String value) {
        if (value == null) return "";
        return Normalizer.normalize(value, Normalizer.Form.NFD)
            .replaceAll("\\p{M}+", "").toLowerCase(Locale.ROOT).trim().replaceAll("\\s+", " ");
    }
    public static boolean matches(String text, String query) {
        String haystack = normalize(text), words = normalize(query);
        if (words.isEmpty()) return true;
        for (String word : words.split(" ")) if (!haystack.contains(word)) return false;
        return true;
    }
    /** Unknown/duplicate/stale IDs cannot create content. Locked sections retain their server slots. */
    public static List<Section> ordered(List<Section> server, List<String> preferences) {
        if (server == null) return Collections.emptyList();
        Map<String,Section> movable = new LinkedHashMap<>();
        Set<String> unique = new HashSet<>();
        for (Section s : server) {
            if (!unique.add(s.id)) throw new IllegalArgumentException("duplicate section");
            if (!s.locked) movable.put(s.id, s);
        }
        List<Section> selected = new ArrayList<>();
        if (preferences != null) for (String id : preferences) {
            Section s = movable.remove(id); if (s != null) selected.add(s);
        }
        selected.addAll(movable.values());
        Iterator<Section> it = selected.iterator();
        List<Section> out = new ArrayList<>();
        for (Section s : server) out.add(s.locked ? s : it.next());
        return out;
    }
    public static boolean visible(Section s, Set<String> hidden, String query) {
        if (s.locked) return true;
        return (hidden == null || !hidden.contains(s.id)) && matches(s.title+" "+s.searchText, query);
    }
    public static List<String> move(List<Section> server, List<String> saved, String id, int direction) {
        List<Section> current = ordered(server, saved); List<String> ids = new ArrayList<>();
        for (Section s : current) if (!s.locked) ids.add(s.id);
        int i = ids.indexOf(id), j = i + (direction < 0 ? -1 : 1);
        if (i >= 0 && j >= 0 && j < ids.size()) Collections.swap(ids, i, j);
        return ids;
    }
    public static List<String> decodeOrder(String saved) {
        if (saved == null || saved.length() > 8192) return Collections.emptyList();
        Set<String> out = new LinkedHashSet<>();
        for (String id : saved.split("\\|")) if (id.matches("[a-z0-9_-]{1,64}")) out.add(id);
        return new ArrayList<>(out);
    }
    public static String encodeOrder(List<String> order) {
        return String.join("|", decodeOrder(order == null ? "" : String.join("|", order)));
    }
    public static String preferenceKey(long account) {
        if (account <= 0) throw new IllegalArgumentException("signed-in account required");
        return "svoyi_home249_test_jkunis_eu_" + account;
    }
    public static boolean twoColumns(float contentWidthDp, float fontScale, boolean preferGrid) {
        return preferGrid && contentWidthDp >= 360f && fontScale <= 1.15f;
    }
    public static boolean canResume(String id, long storedAt, long now, List<Section> server, Set<String> hidden) {
        if (id == null || storedAt <= 0 || now < storedAt || now - storedAt > 86400000L) return false;
        for (Section s : server) if (s.id.equals(id)) return visible(s, hidden, "");
        return false;
    }
    public static String locale(String value) {
        String v = value == null ? "" : value.toLowerCase(Locale.ROOT);
        return v.startsWith("cs") || v.startsWith("cz") ? "cs" : v.startsWith("en") ? "en" : "uk";
    }
    /** Only known same-origin HTTPS entry routes may be altered. */
    public static String jobRoute(String original) {
        if (original == null || original.isEmpty()) return "";
        try {
            URI u = new URI(original);
            if (u.isOpaque() || u.getUserInfo() != null ||
                (u.getRawAuthority()!=null && u.getHost()==null) ||
                (u.getHost()!=null && (!u.getHost().equalsIgnoreCase("test.jkunis.eu") || !"https".equalsIgnoreCase(u.getScheme()))) ||
                (u.getPort()!=-1 && u.getPort()!=443)) return original;
            String path = u.getPath();
            if (path != null && !(path.isEmpty() || path.equals("/") || path.equals("/index.php"))) return original;
            LinkedHashMap<String,List<String>> params = parameters(u.getRawQuery());
            String page = first(params,"p");
            if (!page.isEmpty() && !page.equals("home")) return original;
            if (!(first(params,"view").equals("jobs") || "job-search".equals(u.getFragment()))) return original;
            List<String> kept = new ArrayList<>();
            String raw = u.getRawQuery();
            if (raw != null) for (String pair : raw.split("&")) {
                String key = decode(pair.split("=",2)[0]);
                if (!(key.equals("native") || key.equals("view") || key.equals("p"))) kept.add(pair);
            }
            kept.add("p=home"); kept.add("native=jobs");
            String prefix = u.getScheme()==null ? "" : "https://"+u.getRawAuthority();
            return prefix+(path==null||path.isEmpty()?"/":path)+"?"+String.join("&",kept);
        } catch (IllegalArgumentException | URISyntaxException e) { return original; }
    }
    private static LinkedHashMap<String,List<String>> parameters(String raw) {
        LinkedHashMap<String,List<String>> out = new LinkedHashMap<>();
        if (raw == null) return out;
        for (String pair : raw.split("&")) {
            String[] parts = pair.split("=",2);
            out.computeIfAbsent(decode(parts[0]), k->new ArrayList<>()).add(parts.length==2?decode(parts[1]):"");
        }
        return out;
    }
    private static String decode(String value) {
        try { return URLDecoder.decode(value,"UTF-8"); }
        catch (java.io.UnsupportedEncodingException e) { throw new IllegalStateException(e); }
    }
    private static String first(Map<String,List<String>> map,String key) {
        List<String> all=map.get(key); return all==null||all.isEmpty()?"":all.get(0);
    }
}
