import UIKit
import WebKit
import AVFoundation

/// Shared-site UI inside an iOS host. Website navigation, authentication and themes remain owned by the site.
final class SiteViewController: UIViewController, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate {
    private(set) var web: WKWebView!
    private let toolbar = UIView()
    private let menuButton = UIButton(type: .system)
    private let settingsButton = UIButton(type: .system)
    private let progress = UIProgressView(progressViewStyle: .bar)
    private let errorPanel = UIStackView()
    private let errorLabel = UILabel()
    private var toolbarHeight: NSLayoutConstraint!
    private var webBottom: NSLayoutConstraint!
    private var progressObservation: NSKeyValueObservation?
    private var loadingWork: DispatchWorkItem?
    private var lastURL = SitePolicy.home
    private var documentGeneration = 0
    private var pageIsDark = false
    private var downloads: [ObjectIdentifier: (WKDownload, URL?)] = [:]
    private var mediaRequest: (id: UUID, generation: Int, completion: (WKPermissionDecision) -> Void)?
    private lazy var bridge = HostBridgeProxy(host: self)

    override var preferredStatusBarStyle: UIStatusBarStyle { pageIsDark ? .lightContent : .darkContent }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        makeToolbar()
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .default()
        config.defaultWebpagePreferences.preferredContentMode = .mobile
        config.defaultWebpagePreferences.allowsContentJavaScript = true
        config.preferences.javaScriptCanOpenWindowsAutomatically = false
        config.allowsInlineMediaPlayback = true
        config.allowsAirPlayForMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = .all
        // Standard iPhone UA: do not activate Android/native routes that can hide site panels.
        config.userContentController.addScriptMessageHandler(bridge, contentWorld: .page, name: "svoyiHost")
        if let url = Bundle.main.url(forResource: "HostBridge", withExtension: "js"),
           let source = try? String(contentsOf: url, encoding: .utf8) {
            config.userContentController.addUserScript(WKUserScript(source: source, injectionTime: .atDocumentStart,
                                                                   forMainFrameOnly: true))
        }
        web = WKWebView(frame: .zero, configuration: config)
        web.translatesAutoresizingMaskIntoConstraints = false
        web.navigationDelegate = self
        web.uiDelegate = self
        web.allowsBackForwardNavigationGestures = true
        web.scrollView.contentInsetAdjustmentBehavior = .never
        web.isOpaque = false
        web.backgroundColor = .systemBackground
        // No CSS injection to remove/replace site menus, bottom bars or avatars.
        view.addSubview(web)
        webBottom = web.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor)
        NSLayoutConstraint.activate([
            web.topAnchor.constraint(equalTo: toolbar.bottomAnchor), web.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            web.trailingAnchor.constraint(equalTo: view.trailingAnchor), webBottom
        ])
        progress.translatesAutoresizingMaskIntoConstraints = false
        progress.isHidden = true
        view.addSubview(progress)
        NSLayoutConstraint.activate([
            progress.topAnchor.constraint(equalTo: web.topAnchor), progress.leadingAnchor.constraint(equalTo: web.leadingAnchor),
            progress.trailingAnchor.constraint(equalTo: web.trailingAnchor)
        ])
        makeErrorPanel()
        progressObservation = web.observe(\.estimatedProgress, options: [.new]) { [weak self] web, _ in
            DispatchQueue.main.async { self?.progress.setProgress(Float(web.estimatedProgress), animated: true) }
        }
        NotificationCenter.default.addObserver(self, selector: #selector(keyboardChanged(_:)),
                                               name: UIResponder.keyboardWillChangeFrameNotification, object: nil)
        NotificationCenter.default.addObserver(self, selector: #selector(keyboardHidden(_:)),
                                               name: UIResponder.keyboardWillHideNotification, object: nil)
        open(SitePolicy.home)
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
        loadingWork?.cancel()
    }

    private func makeToolbar() {
        toolbar.translatesAutoresizingMaskIntoConstraints = false
        toolbar.backgroundColor = .secondarySystemBackground
        view.addSubview(toolbar)
        toolbarHeight = toolbar.heightAnchor.constraint(equalToConstant: 44)
        NSLayoutConstraint.activate([
            toolbar.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            toolbar.leadingAnchor.constraint(equalTo: view.leadingAnchor), toolbar.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            toolbarHeight
        ])
        menuButton.setImage(UIImage(systemName: "line.3.horizontal"), for: .normal)
        menuButton.accessibilityLabel = "Відкрити меню сайту"
        menuButton.addTarget(self, action: #selector(openSiteMenu), for: .touchUpInside)
        settingsButton.setImage(UIImage(systemName: "gearshape"), for: .normal)
        settingsButton.accessibilityLabel = "Налаштування застосунку"
        settingsButton.addTarget(self, action: #selector(openSettings), for: .touchUpInside)
        [menuButton, settingsButton].forEach {
            $0.translatesAutoresizingMaskIntoConstraints = false
            $0.tintColor = .label
            toolbar.addSubview($0)
        }
        NSLayoutConstraint.activate([
            menuButton.leadingAnchor.constraint(equalTo: toolbar.safeAreaLayoutGuide.leadingAnchor, constant: 6),
            settingsButton.trailingAnchor.constraint(equalTo: toolbar.safeAreaLayoutGuide.trailingAnchor, constant: -6),
            menuButton.centerYAnchor.constraint(equalTo: toolbar.centerYAnchor), settingsButton.centerYAnchor.constraint(equalTo: toolbar.centerYAnchor),
            menuButton.heightAnchor.constraint(equalToConstant: 44), menuButton.widthAnchor.constraint(equalToConstant: 48),
            settingsButton.heightAnchor.constraint(equalToConstant: 44), settingsButton.widthAnchor.constraint(equalToConstant: 48)
        ])
        // The site's own header remains visible below this compact control strip.
        toolbar.clipsToBounds = true
    }

    private func makeErrorPanel() {
        errorPanel.axis = .vertical
        errorPanel.alignment = .center
        errorPanel.spacing = 18
        errorPanel.translatesAutoresizingMaskIntoConstraints = false
        errorPanel.backgroundColor = .systemBackground
        errorPanel.isLayoutMarginsRelativeArrangement = true
        errorPanel.layoutMargins = UIEdgeInsets(top: 24, left: 24, bottom: 24, right: 24)
        errorPanel.layer.cornerRadius = 16
        let icon = UIImageView(image: UIImage(systemName: "wifi.exclamationmark"))
        icon.preferredSymbolConfiguration = UIImage.SymbolConfiguration(pointSize: 32)
        icon.tintColor = .secondaryLabel
        errorLabel.font = .preferredFont(forTextStyle: .body)
        errorLabel.adjustsFontForContentSizeCategory = true
        errorLabel.numberOfLines = 0
        errorLabel.textAlignment = .center
        let retry = UIButton(type: .system)
        retry.setTitle("Спробувати знову", for: .normal)
        retry.addTarget(self, action: #selector(retryPage), for: .touchUpInside)
        [icon, errorLabel, retry].forEach(errorPanel.addArrangedSubview)
        view.addSubview(errorPanel)
        NSLayoutConstraint.activate([
            errorPanel.centerXAnchor.constraint(equalTo: web.centerXAnchor),
            errorPanel.centerYAnchor.constraint(equalTo: web.centerYAnchor),
            errorPanel.widthAnchor.constraint(lessThanOrEqualToConstant: 420),
            errorPanel.leadingAnchor.constraint(greaterThanOrEqualTo: view.leadingAnchor, constant: 20),
            errorPanel.trailingAnchor.constraint(lessThanOrEqualTo: view.trailingAnchor, constant: -20)
        ])
        errorPanel.isHidden = true
    }

    func open(_ url: URL) {
        guard SitePolicy.isTrusted(url) else { return }
        lastURL = url
        errorPanel.isHidden = true
        web.load(URLRequest(url: url, cachePolicy: .useProtocolCachePolicy, timeoutInterval: 35))
    }

    @objc private func retryPage() { open(lastURL) }
    @objc private func openSettings() {
        guard presentedViewController == nil else { return }
        let settings = SettingsViewController(host: self)
        let nav = UINavigationController(rootViewController: settings)
        nav.modalPresentationStyle = .pageSheet
        present(nav, animated: true)
    }

    @objc private func openSiteMenu() {
        guard SitePolicy.isTrusted(web.url) else { return }
        let script = """
        (()=>{for(const id of ['r44Menu','appMoreBtn','classicMobileToggle','desktopDrawerBtn','svDesktopMenu']){
        const b=document.getElementById(id);if(b){b.click();return 'opened';}}
        return document.body.classList.contains('guest-user')?'guest':'missing';})()
        """
        web.evaluateJavaScript(script) { [weak self] result, _ in
            guard let self else { return }
            if result as? String != "opened" {
                self.notice("Меню сайту", result as? String == "guest"
                    ? "Бічне меню та панель акаунта з’являються після входу. Увійдіть через форму на сторінці."
                    : "На цій сторінці сайт не надав бічне меню. Його панелі застосунок не приховує.")
            }
        }
    }

    @objc private func keyboardChanged(_ note: Notification) {
        guard let frame = note.userInfo?[UIResponder.keyboardFrameEndUserInfoKey] as? CGRect,
              let window = view.window else { return }
        let converted = view.convert(frame, from: window.screen.coordinateSpace)
        let intersection = view.bounds.intersection(converted)
        let overlapsBottom = !intersection.isNull && converted.maxY >= view.bounds.maxY - 1
        let overlap = overlapsBottom ? max(0, view.bounds.maxY - converted.minY - view.safeAreaInsets.bottom) : 0
        applyKeyboard(overlap, note: note)
    }

    @objc private func keyboardHidden(_ note: Notification) { applyKeyboard(0, note: note) }
    private func applyKeyboard(_ overlap: CGFloat, note: Notification) {
        webBottom.constant = -overlap
        toolbarHeight.constant = overlap > 0 ? 0 : 44
        let duration = note.userInfo?[UIResponder.keyboardAnimationDurationUserInfoKey] as? Double ?? 0.25
        UIView.animate(withDuration: duration) { self.view.layoutIfNeeded() }
    }

    private func stoppedLoading() {
        loadingWork?.cancel()
        progress.isHidden = true
    }

    func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
        documentGeneration += 1
        finishMedia(.deny)
        errorPanel.isHidden = true
        loadingWork?.cancel()
        let work = DispatchWorkItem { [weak self] in
            guard let self, self.web.isLoading else { return }
            self.progress.isHidden = false
        }
        loadingWork = work
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2, execute: work)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        stoppedLoading()
        if let url = webView.url, SitePolicy.isTrusted(url) { lastURL = url }
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) { loadFailed(error) }
    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) { loadFailed(error) }
    private func loadFailed(_ error: Error) {
        stoppedLoading()
        guard (error as NSError).code != NSURLErrorCancelled else { return }
        finishMedia(.deny)
        errorLabel.text = "Не вдалося відкрити сторінку. Перевірте інтернет і спробуйте знову. Незбережені поля можуть бути втрачені."
        errorPanel.isHidden = false
    }

    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        stoppedLoading()
        documentGeneration += 1
        finishMedia(.deny)
        errorLabel.text = "iOS зупинила сторінку. Натисніть «Спробувати знову», щоб відкрити її. Незбережені поля могли бути втрачені."
        errorPanel.isHidden = false
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = action.request.url else { decisionHandler(.cancel); return }
        if action.targetFrame?.isMainFrame == false {
            // Embed resources retain WebKit's same-origin and ATS restrictions. No bridge/media grants to embeds.
            let allowed = ["https", "about", "blob", "data"].contains(url.scheme?.lowercased() ?? "")
            decisionHandler(allowed ? .allow : .cancel)
            return
        }
        if SitePolicy.isTrusted(url) {
            if action.shouldPerformDownload { decisionHandler(.download); return }
            if action.targetFrame == nil { decisionHandler(.cancel); open(url); return }
            decisionHandler(.allow)
        } else if url.scheme == "blob", SitePolicy.isTrusted(webView.url), action.shouldPerformDownload {
            decisionHandler(.download)
        } else {
            decisionHandler(.cancel)
            if SitePolicy.canOpenExternally(url) { confirmExternal(url) }
        }
    }

    func webView(_ webView: WKWebView, decidePolicyFor response: WKNavigationResponse,
                 decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        guard response.isForMainFrame else { decisionHandler(.allow); return }
        let url = response.response.url
        guard SitePolicy.isTrusted(url) || (url?.scheme == "blob" && SitePolicy.isTrusted(webView.url)) else {
            decisionHandler(.cancel); return
        }
        let attachment = (response.response as? HTTPURLResponse)?.value(forHTTPHeaderField: "Content-Disposition")?
            .lowercased().hasPrefix("attachment") == true
        decisionHandler(!response.canShowMIMEType || attachment ? .download : .allow)
    }

    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        guard let url = action.request.url else { return nil }
        if SitePolicy.isTrusted(url) { open(url) }
        else if SitePolicy.canOpenExternally(url) { confirmExternal(url) }
        return nil
    }

    private func confirmExternal(_ url: URL) {
        guard presentedViewController == nil else { return }
        let alert = UIAlertController(title: "Відкрити поза застосунком?",
                                      message: url.host ?? url.scheme, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Скасувати", style: .cancel))
        alert.addAction(UIAlertAction(title: "Відкрити", style: .default) { _ in
            UIApplication.shared.open(url, options: [:])
        })
        present(alert, animated: true)
    }

    func notice(_ title: String, _ message: String) {
        guard presentedViewController == nil else { return }
        let alert = UIAlertController(title: title, message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Добре", style: .default))
        present(alert, animated: true)
    }

    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        guard frame.isMainFrame, SitePolicy.isTrusted(frame.request.url), presentedViewController == nil else { completionHandler(); return }
        let alert = UIAlertController(title: "Свої", message: String(message.prefix(4000)), preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Добре", style: .default) { _ in completionHandler() })
        present(alert, animated: true)
    }

    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        guard frame.isMainFrame, SitePolicy.isTrusted(frame.request.url), presentedViewController == nil else { completionHandler(false); return }
        let alert = UIAlertController(title: "Свої", message: String(message.prefix(4000)), preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Скасувати", style: .cancel) { _ in completionHandler(false) })
        alert.addAction(UIAlertAction(title: "Підтвердити", style: .default) { _ in completionHandler(true) })
        present(alert, animated: true)
    }

    func webView(_ webView: WKWebView, runJavaScriptTextInputPanelWithPrompt prompt: String, defaultText: String?,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (String?) -> Void) {
        guard frame.isMainFrame, SitePolicy.isTrusted(frame.request.url), presentedViewController == nil else { completionHandler(nil); return }
        let alert = UIAlertController(title: "Свої", message: String(prompt.prefix(2000)), preferredStyle: .alert)
        alert.addTextField { $0.text = defaultText }
        alert.addAction(UIAlertAction(title: "Скасувати", style: .cancel) { _ in completionHandler(nil) })
        alert.addAction(UIAlertAction(title: "Добре", style: .default) { [weak alert] _ in completionHandler(alert?.textFields?.first?.text) })
        present(alert, animated: true)
    }

    func webView(_ webView: WKWebView, requestMediaCapturePermissionFor origin: WKSecurityOrigin,
                 initiatedByFrame frame: WKFrameInfo, type: WKMediaCaptureType,
                 decisionHandler: @escaping (WKPermissionDecision) -> Void) {
        guard SitePolicy.isTrusted(webView.url), frame.isMainFrame, SitePolicy.isTrusted(frame.request.url),
              origin.protocol == "https", origin.host == SitePolicy.host, (origin.port == 0 || origin.port == 443),
              mediaRequest == nil else { decisionHandler(.deny); return }
        let types: [AVMediaType]
        switch type {
        case .camera: types = [.video]
        case .microphone: types = [.audio]
        case .cameraAndMicrophone: types = [.video, .audio]
        @unknown default: decisionHandler(.deny); return
        }
        let id = UUID()
        mediaRequest = (id, documentGeneration, decisionHandler)
        requestMedia(types, index: 0, id: id)
    }

    private func requestMedia(_ types: [AVMediaType], index: Int, id: UUID) {
        guard let pending = mediaRequest, pending.id == id else { return }
        guard pending.generation == documentGeneration, SitePolicy.isTrusted(web.url) else { finishMedia(.deny); return }
        guard index < types.count else { finishMedia(.grant); return }
        let mediaType = types[index]
        switch AVCaptureDevice.authorizationStatus(for: mediaType) {
        case .authorized: requestMedia(types, index: index + 1, id: id)
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: mediaType) { [weak self] granted in
                DispatchQueue.main.async {
                    guard let self, self.mediaRequest?.id == id else { return }
                    if granted { self.requestMedia(types, index: index + 1, id: id) }
                    else { self.finishMedia(.deny) }
                }
            }
        default: finishMedia(.deny)
        }
    }

    private func finishMedia(_ decision: WKPermissionDecision) {
        let callback = mediaRequest?.completion
        mediaRequest = nil
        callback?(decision)
    }

    func webView(_ webView: WKWebView, navigationAction: WKNavigationAction, didBecome download: WKDownload) { track(download) }
    func webView(_ webView: WKWebView, navigationResponse: WKNavigationResponse, didBecome download: WKDownload) { track(download) }
    private func track(_ download: WKDownload) {
        stoppedLoading()
        download.delegate = self
        downloads[ObjectIdentifier(download)] = (download, nil)
    }

    func download(_ download: WKDownload, decideDestinationUsing response: URLResponse, suggestedFilename: String,
                  completionHandler: @escaping (URL?) -> Void) {
        do {
            let dir = FileManager.default.temporaryDirectory.appendingPathComponent("SvoyiDownloads", isDirectory: true)
                .appendingPathComponent(UUID().uuidString, isDirectory: true)
            try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            let url = dir.appendingPathComponent(SitePolicy.downloadName(suggestedFilename))
            downloads[ObjectIdentifier(download)] = (download, url)
            completionHandler(url)
        } catch {
            completionHandler(nil)
            notice("Файл", "Не вдалося підготувати місце для файлу.")
        }
    }

    func downloadDidFinish(_ download: WKDownload) {
        guard let item = downloads.removeValue(forKey: ObjectIdentifier(download)), let url = item.1 else { return }
        share([url]) { _ in }
    }

    func download(_ download: WKDownload, didFailWithError error: Error, resumeData: Data?) {
        if let url = downloads.removeValue(forKey: ObjectIdentifier(download))?.1 {
            try? FileManager.default.removeItem(at: url.deletingLastPathComponent())
        }
        notice("Файл", "Завантаження не завершено. Спробуйте ще раз.")
    }

    func share(_ items: [Any], completion: @escaping (Bool) -> Void) {
        guard !items.isEmpty, presentedViewController == nil else { completion(false); return }
        let sheet = UIActivityViewController(activityItems: items, applicationActivities: nil)
        if let popover = sheet.popoverPresentationController {
            popover.sourceView = settingsButton
            popover.sourceRect = settingsButton.bounds
        }
        sheet.completionWithItemsHandler = { _, completed, _, _ in completion(completed) }
        present(sheet, animated: true)
    }

    fileprivate func handleBridge(_ message: WKScriptMessage, reply: @escaping (Any?, String?) -> Void) {
        guard message.frameInfo.isMainFrame, SitePolicy.isTrusted(message.frameInfo.request.url),
              SitePolicy.isTrusted(web.url), let body = message.body as? [String: Any], let type = body["type"] as? String else {
            reply(nil, "Untrusted origin"); return
        }
        switch type {
        case "theme":
            guard let rgb = body["rgb"] as? [Double], rgb.count == 3,
                  rgb.allSatisfy({ $0.isFinite && $0 >= 0 && $0 <= 255 }) else { reply(nil, "Invalid theme"); return }
            let color = UIColor(red: CGFloat(rgb[0] / 255), green: CGFloat(rgb[1] / 255), blue: CGFloat(rgb[2] / 255), alpha: 1)
            pageIsDark = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) < 140
            view.backgroundColor = color
            web.backgroundColor = color
            toolbar.backgroundColor = color
            [menuButton, settingsButton].forEach { $0.tintColor = pageIsDark ? .white : .black }
            setNeedsStatusBarAppearanceUpdate()
            reply(["ok": true], nil)
        case "share":
            var items: [Any] = []
            let title = String((body["title"] as? String ?? "").prefix(200))
            let text = String((body["text"] as? String ?? "").prefix(10000))
            if !title.isEmpty { items.append(title) }
            if !text.isEmpty { items.append(text) }
            let raw = body["url"] as? String ?? ""
            if !raw.isEmpty {
                guard let url = SitePolicy.shareURL(raw) else { reply(nil, "Unsupported URL"); return }
                items.append(url)
            }
            share(items) { completed in reply(["completed": completed], nil) }
        default: reply(nil, "Unsupported operation")
        }
    }
}

private final class HostBridgeProxy: NSObject, WKScriptMessageHandlerWithReply {
    weak var host: SiteViewController?
    init(host: SiteViewController) { self.host = host }
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage,
                               replyHandler: @escaping (Any?, String?) -> Void) {
        guard let host else { replyHandler(nil, "Host closed"); return }
        host.handleBridge(message, reply: replyHandler)
    }
}
