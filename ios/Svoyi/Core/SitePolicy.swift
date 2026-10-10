import Foundation

/// Only this exact HTTPS origin is allowed to access the native bridge or device permissions.
enum SitePolicy {
    static let host = "test.jkunis.eu"
    static let home = URL(string: "https://test.jkunis.eu/")!

    static func isTrusted(_ url: URL?) -> Bool {
        guard let url, let c = URLComponents(url: url, resolvingAgainstBaseURL: true),
              c.scheme?.lowercased() == "https", c.host?.lowercased() == host,
              c.port == nil || c.port == 443, c.user == nil, c.password == nil else { return false }
        // Reject ambiguous/encoded authorities and URL parser differences.
        guard let authority = url.absoluteString.components(separatedBy: "://").dropFirst().first?
                .components(separatedBy: CharacterSet(charactersIn: "/?#")).first,
              !authority.contains("%"), !authority.contains("\\"), !authority.contains("@") else { return false }
        return true
    }

    static func canOpenExternally(_ url: URL) -> Bool {
        guard let c = URLComponents(url: url, resolvingAgainstBaseURL: true),
              c.user == nil, c.password == nil else { return false }
        switch c.scheme?.lowercased() {
        case "http", "https": return !(c.host ?? "").isEmpty
        case "mailto", "tel": return !c.path.isEmpty
        default: return false
        }
    }

    /// Preserve filename only, never a server-supplied directory or a hidden path.
    static func downloadName(_ suggested: String) -> String {
        let leaf = suggested.replacingOccurrences(of: "\\", with: "/")
            .components(separatedBy: "/").last ?? ""
        let cleaned = leaf.unicodeScalars.filter {
            !CharacterSet.controlCharacters.contains($0) && !"/:".unicodeScalars.contains($0)
        }.map(String.init).joined().trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleaned.isEmpty, cleaned != ".", cleaned != "..", !cleaned.hasPrefix(".") else { return "file" }
        return String(cleaned.prefix(120))
    }

    static func shareURL(_ raw: String) -> URL? {
        guard raw.count <= 4096, let url = URL(string: raw, relativeTo: home)?.absoluteURL,
              let scheme = url.scheme?.lowercased(), ["https", "http"].contains(scheme),
              canOpenExternally(url) else { return nil }
        return url
    }
}
