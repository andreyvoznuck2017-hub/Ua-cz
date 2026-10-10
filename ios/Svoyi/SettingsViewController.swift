import UIKit
import AVFoundation
import CoreLocation
import UserNotifications

final class SettingsViewController: UITableViewController, CLLocationManagerDelegate {
    private weak var host: SiteViewController?
    private let location = CLLocationManager()
    private var notificationStatus = "Перевіряємо дозвіл…"

    init(host: SiteViewController) {
        self.host = host
        super.init(style: .insetGrouped)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Налаштування застосунку"
        navigationItem.rightBarButtonItem = UIBarButtonItem(title: "Готово", style: .done, target: self, action: #selector(close))
        location.delegate = self
        NotificationCenter.default.addObserver(self, selector: #selector(refresh),
                                               name: UIApplication.didBecomeActiveNotification, object: nil)
        refresh()
    }
    deinit { NotificationCenter.default.removeObserver(self) }
    @objc private func close() { dismiss(animated: true) }
    @objc private func refresh() {
        UNUserNotificationCenter.current().getNotificationSettings { [weak self] settings in
            DispatchQueue.main.async {
                guard let self else { return }
                switch settings.authorizationStatus {
                case .authorized, .provisional, .ephemeral: self.notificationStatus = "Системний дозвіл надано"
                case .denied: self.notificationStatus = "Заборонено в iOS"
                case .notDetermined: self.notificationStatus = "Ще не запитували"
                @unknown default: self.notificationStatus = "Невідомий стан"
                }
                self.tableView.reloadData()
            }
        }
        tableView.reloadData()
    }

    override func numberOfSections(in tableView: UITableView) -> Int { 4 }
    override func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int { [4, 4, 3, 2][section] }
    override func tableView(_ tableView: UITableView, titleForHeaderInSection section: Int) -> String? {
        ["Сторінка", "Дозволи iPhone", "Сповіщення та дзвінки", "Про застосунок"][section]
    }
    override func tableView(_ tableView: UITableView, titleForFooterInSection section: Int) -> String? {
        switch section {
        case 0: return "Панелі, мова й усі теми залишаються налаштуваннями сайту. Оновлення сторінки може видалити незбережений текст."
        case 1: return "Дозволи запитуються лише після вашої дії. Вибір фото/файлів виконується системним вікном iOS."
        case 2: return "Локальний тест не означає, що push із сайту працюють. APNs, відповіді зі сповіщень і фонові дзвінки ще не підключені."
        default: return "Тестовий iOS-клієнт зі спільним вебінтерфейсом. Не є повністю переписаним нативним інтерфейсом."
        }
    }

    override func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = UITableViewCell(style: .subtitle, reuseIdentifier: nil)
        let item: (String, String, String)
        switch (indexPath.section, indexPath.row) {
        case (0, 0): item = ("Назад", "Попередня сторінка", "chevron.backward")
        case (0, 1): item = ("Головна", SitePolicy.host, "house")
        case (0, 2): item = ("Оновити сторінку", "Перед оновленням збережіть написане", "arrow.clockwise")
        case (0, 3): item = ("Поділитися сторінкою", "Системне меню iOS", "square.and.arrow.up")
        case (1, 0): item = ("Камера", mediaStatus(.video), "camera")
        case (1, 1): item = ("Мікрофон", mediaStatus(.audio), "mic")
        case (1, 2): item = ("Місцезнаходження", locationStatus(), "location")
        case (1, 3): item = ("Відкрити налаштування iOS", "Змінити дозволи застосунку", "gearshape")
        case (2, 0): item = ("Дозвіл на сповіщення", notificationStatus, "bell")
        case (2, 1): item = ("Локальне тестове сповіщення", "Лише перевірка цього iPhone", "bell.badge")
        case (2, 2): item = ("Push і дзвінки у фоні", "Не підключені в цій версії", "phone.badge.waveform")
        case (3, 0): item = ("Свої в Європі", "iOS 1.0.1 · тестовий клієнт", "info.circle")
        default: item = ("Сайт", SitePolicy.host, "globe")
        }
        cell.textLabel?.text = item.0
        cell.textLabel?.numberOfLines = 0
        cell.textLabel?.font = .preferredFont(forTextStyle: .body)
        cell.detailTextLabel?.text = item.1
        cell.detailTextLabel?.numberOfLines = 0
        cell.detailTextLabel?.font = .preferredFont(forTextStyle: .caption1)
        cell.imageView?.image = UIImage(systemName: item.2)
        cell.imageView?.tintColor = .label
        cell.accessoryType = indexPath.section == 3 || (indexPath.section == 2 && indexPath.row == 2) ? .none : .disclosureIndicator
        cell.selectionStyle = indexPath.section == 3 ? .none : .default
        return cell
    }

    override func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        switch (indexPath.section, indexPath.row) {
        case (0, 0):
            guard host?.web.canGoBack == true else { message("Назад", "Попередньої сторінки ще немає."); return }
            dismiss(animated: true) { [weak host] in host?.web.goBack() }
        case (0, 1): confirmNavigation { [weak host] in host?.open(SitePolicy.home) }
        case (0, 2): confirmNavigation { [weak host] in host?.web.reload() }
        case (0, 3):
            guard let url = host?.web.url, SitePolicy.isTrusted(url) else { return }
            dismiss(animated: true) { [weak host] in host?.share([url]) { _ in } }
        case (1, 0): askMedia(.video)
        case (1, 1): askMedia(.audio)
        case (1, 2):
            if location.authorizationStatus == .notDetermined { location.requestWhenInUseAuthorization() }
            else { openSystemSettings() }
        case (1, 3): openSystemSettings()
        case (2, 0): requestNotifications(test: false)
        case (2, 1): requestNotifications(test: true)
        case (2, 2): message("Потрібне підключення Apple", "Ця версія ще не отримує серверні push і не приймає дзвінки у фоні. Вебдзвінки у відкритому застосунку потребують перевірки на iPhone.")
        default: break
        }
    }

    private func confirmNavigation(_ action: @escaping () -> Void) {
        let alert = UIAlertController(title: "Перейти зі сторінки?", message: "Незбережений текст може бути втрачений.", preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Скасувати", style: .cancel))
        alert.addAction(UIAlertAction(title: "Продовжити", style: .default) { [weak self] _ in
            self?.navigationController?.presentingViewController?.dismiss(animated: true, completion: action)
        })
        present(alert, animated: true)
    }
    private func mediaStatus(_ type: AVMediaType) -> String {
        switch AVCaptureDevice.authorizationStatus(for: type) {
        case .authorized: return "Дозволено"
        case .notDetermined: return "Ще не запитували"
        case .restricted: return "Обмежено системою"
        case .denied: return "Заборонено — змінити в iOS"
        @unknown default: return "Невідомий стан"
        }
    }
    private func locationStatus() -> String {
        switch location.authorizationStatus {
        case .authorizedAlways, .authorizedWhenInUse: return "Дозволено під час використання"
        case .notDetermined: return "Ще не запитували"
        case .restricted: return "Обмежено системою"
        case .denied: return "Заборонено — змінити в iOS"
        @unknown default: return "Невідомий стан"
        }
    }
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) { tableView.reloadData() }
    private func askMedia(_ type: AVMediaType) {
        if AVCaptureDevice.authorizationStatus(for: type) == .notDetermined {
            AVCaptureDevice.requestAccess(for: type) { [weak self] _ in DispatchQueue.main.async { self?.refresh() } }
        } else { openSystemSettings() }
    }
    private func requestNotifications(test: Bool) {
        NotificationCoordinator.shared.requestPermission { [weak self] granted, error in
            guard let self else { return }
            self.refresh()
            guard error == nil, granted else {
                self.message("Сповіщення", "Дозвіл не надано. Його можна змінити у налаштуваннях iOS."); return
            }
            if test {
                NotificationCoordinator.shared.sendLocalTest { [weak self] error in
                    if error != nil { self?.message("Тест", "Не вдалося створити локальне сповіщення.") }
                }
            }
        }
    }
    private func openSystemSettings() {
        guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
        UIApplication.shared.open(url, options: [:])
    }
    private func message(_ title: String, _ text: String) {
        guard presentedViewController == nil else { return }
        let alert = UIAlertController(title: title, message: text, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "Добре", style: .default))
        present(alert, animated: true)
    }
}
