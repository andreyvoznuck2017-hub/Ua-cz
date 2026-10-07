package eu.svoyi.nativeapp;

import java.net.URI;
import java.net.URLDecoder;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/** Current server profile links include a filter-preserving, local back route. */
public final class DatingRoute256 {
    private DatingRoute256() {}
    private static final String ORIGIN = "https://test.jkunis.eu";
    private static final Set<String> TABS = new HashSet<>(Arrays.asList(
            "discover", "matches", "likes", "favorites", "views", "random", "sent"));
    private static final Set<String> PROFILE = new HashSet<>(Arrays.asList("p", "view", "from", "back"));
    private static final Set<String> FILTERS = new HashSet<>(Arrays.asList(
            "p", "tab", "city", "country", "gender", "goal", "age_from", "age_to", "radius", "near", "online"));

    private static URI local(String route, String origin) throws Exception {
        if (route == null || route.trim().isEmpty() || origin == null) throw new Exception("empty route");
        URI base = new URI(origin);
        URI uri = base.resolve(route.trim());
        if (uri.isOpaque() || uri.getUserInfo() != null || uri.getFragment() != null
                || !base.getScheme().equals(uri.getScheme()) || base.getHost() == null
                || !base.getHost().equalsIgnoreCase(uri.getHost()) || base.getPort() != uri.getPort()) {
            throw new Exception("nonlocal route");
        }
        String path = uri.getPath();
        if (!("".equals(path) || "/".equals(path) || "/index.php".equals(path))) throw new Exception("path");
        return uri;
    }

    private static Map<String, String> query(URI uri) throws Exception {
        Map<String, String> result = new LinkedHashMap<>();
        if (uri.getRawQuery() == null) throw new Exception("query missing");
        for (String part : uri.getRawQuery().split("&", -1)) {
            String[] pair = part.split("=", 2);
            String key = URLDecoder.decode(pair[0], "UTF-8");
            String value = pair.length == 2 ? URLDecoder.decode(pair[1], "UTF-8") : "";
            if (key.isEmpty() || result.containsKey(key)) throw new Exception("duplicate or empty key");
            result.put(key, value);
        }
        return result;
    }

    private static String back(String value, String origin) throws Exception {
        URI uri = local(value, origin);
        Map<String, String> fields = query(uri);
        if (!FILTERS.containsAll(fields.keySet()) || !"dating".equals(fields.get("p"))
                || (fields.containsKey("tab") && !TABS.contains(fields.get("tab")))) throw new Exception("back route");
        String path = uri.getRawPath();
        return (path == null || path.isEmpty() ? "/" : path) + "?" + uri.getRawQuery();
    }

    public static boolean profileRoute(int id, String route, String origin) {
        try {
            if (id <= 0) return false;
            Map<String, String> fields = query(local(route, origin));
            if (!PROFILE.containsAll(fields.keySet()) || !"dating".equals(fields.get("p"))
                    || !String.valueOf(id).equals(fields.get("view"))
                    || (fields.containsKey("from") && !TABS.contains(fields.get("from")))) return false;
            if (fields.containsKey("back")) back(fields.get("back"), origin);
            return true;
        } catch (Exception invalid) { return false; }
    }

    public static String tab(String value) {
        return TABS.contains(value) ? value : "discover";
    }

    public static String returnRoute(String route) {
        try {
            Map<String, String> fields = query(local(route, ORIGIN));
            if (fields.containsKey("back")) return back(fields.get("back"), ORIGIN);
            String from = fields.get("from");
            if (TABS.contains(from)) return "/?p=dating&tab=" + from;
        } catch (Exception invalid) { /* Fall back to the local catalog. */ }
        return "/?p=dating&tab=discover";
    }
}
