package eu.svoyi.nativeapp;
import java.net.URLEncoder;
public final class DatingRoute256Test {
    private static void require(boolean condition, String name) {
        if (!condition) throw new AssertionError(name);
    }
    public static void main(String[] args) throws Exception {
        String origin="https://test.jkunis.eu";
        String filters="?p=dating&tab=discover&radius=50&city=&country=&gender=&goal=&age_from=18&age_to=70";
        String live=origin+"/?p=dating&view=3&from=discover&back="+URLEncoder.encode(filters,"UTF-8");
        require(DatingRoute256.profileRoute(3,live,origin),"current server link");
        require(DatingRoute256.returnRoute(live).equals("/"+filters),"all filters survive return");
        require(DatingRoute256.profileRoute(3,"/?p=dating&view=3&from=likes",origin),"legacy relative link");
        require(DatingRoute256.profileRoute(3,"/?p=dating&view=3&from=random",origin),"random link");
        require(DatingRoute256.returnRoute("/?p=dating&view=3&from=random").equals("/?p=dating&tab=random"),"random return");
        require(!DatingRoute256.profileRoute(4,live,origin),"profile identity bound");
        require(!DatingRoute256.profileRoute(0,live,origin),"positive identity");
        String[] bad={
            "https://other.example/?p=dating&view=3", "//other.example/?p=dating&view=3",
            "http://test.jkunis.eu/?p=dating&view=3", "https://test.jkunis.eu:444/?p=dating&view=3",
            "https://user@test.jkunis.eu/?p=dating&view=3", "/other?p=dating&view=3",
            "/?p=dating&view=3#fragment", "/?p=dating&view=3&view=4", "/?p=dating&view=3&%76iew=3",
            "/?p=dating&view=3&action=delete", "/?p=dating&view=3&from=unknown",
            "/?p=dating&view=3&back=https%3A%2F%2Fother.example%2F%3Fp%3Ddating",
            "/?p=dating&view=3&back=%3Fp%3Dprofile", "/?p=dating&view=3&back=%3Fp%3Ddating%26action%3Ddelete",
            "/?p=dating&view=3&back=%3Fp%3Ddating&back=%3Fp%3Ddating",
            "/?p=dating&view=3&back=%3Fp%3Ddating%26tab%3Ddiscover%26tab%3Drandom"
        };
        for(String route:bad)require(!DatingRoute256.profileRoute(3,route,origin),"reject "+route);
        System.out.println("Dating route contract: 23 checks passed");
    }
}
