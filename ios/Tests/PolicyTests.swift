import Foundation
#if canImport(Darwin)
import Darwin
#elseif canImport(Glibc)
import Glibc
#endif

@main
struct PolicyTests {
    static var count = 0
    static func check(_ condition: Bool, _ name: String) {
        count += 1
        guard condition else { print("FAIL: \(name)"); exit(1) }
        print("PASS: \(name)")
    }
    static func main() {
        for value in ["https://test.jkunis.eu/", "https://test.jkunis.eu/?p=mail", "https://test.jkunis.eu:443/a",
                      "https://TEST.JKUNIS.EU/a?q=1", "https://test.jkunis.eu/path%20name"] {
            check(SitePolicy.isTrusted(URL(string: value)), "trusted \(value)")
        }
        for value in ["http://test.jkunis.eu/", "https://test.jkunis.net/", "https://test.jkunis.eu.evil.test/",
                      "https://evil.test/?url=https://test.jkunis.eu/", "https://eviltest.jkunis.eu/",
                      "https://test.jkunis.eu:8443/", "https://test.jkunis.eu./", "https://user@test.jkunis.eu/",
                      "https://user:pass@test.jkunis.eu/", "https://test.jkunis.eu@evil.test/",
                      "file:///test.jkunis.eu", "javascript:alert(1)", "data:text/html,hello",
                      "https://%74est.jkunis.eu/", "https://test.jkunis%2Eeu/", "svoyi://home"] {
            check(!SitePolicy.isTrusted(URL(string: value)), "blocked \(value)")
        }
        check(!SitePolicy.isTrusted(nil), "nil blocked")
        for value in ["https://example.com/a", "http://example.com/", "mailto:test@example.com", "tel:+420123456789"] {
            check(SitePolicy.canOpenExternally(URL(string: value)!), "external allowed \(value)")
        }
        for value in ["javascript:alert(1)", "file:///etc/passwd", "data:text/html,hello", "intent://app",
                      "https://user:pass@example.com", "mailto:", "tel:"] {
            check(!SitePolicy.canOpenExternally(URL(string: value)!), "external blocked \(value)")
        }
        let filenames = [("photo.jpg", "photo.jpg"), ("../../secret.txt", "secret.txt"),
                         ("C:\\folder\\picture.png", "picture.png"), (".secret", "file"), ("..", "file"),
                         ("a/", "file"), ("a\n.txt", "a.txt"), ("Фото Києва.jpg", "Фото Києва.jpg")]
        for (raw, result) in filenames { check(SitePolicy.downloadName(raw) == result, "safe filename \(raw.debugDescription)") }
        check(SitePolicy.downloadName(String(repeating: "a", count: 300)).count == 120, "bounded filename")
        check(SitePolicy.shareURL("/?p=mail")?.host == SitePolicy.host, "relative share URL")
        check(SitePolicy.shareURL("https://example.com/") != nil, "external HTTPS share URL")
        check(SitePolicy.shareURL("javascript:alert(1)") == nil, "reject JS share")
        check(SitePolicy.shareURL("file:///etc/passwd") == nil, "reject file share")
        check(SitePolicy.shareURL(String(repeating: "a", count: 5000)) == nil, "bounded share URL")
        print("POLICY TESTS: \(count) passed")
    }
}
