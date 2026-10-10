import Foundation
import UserNotifications

/// Explicit LOCAL notification test, not production remote push.
final class NotificationCoordinator: NSObject, UNUserNotificationCenterDelegate {
    static let shared = NotificationCoordinator()
    static let localTestID = "svoyi.explicit-local-test"

    func requestPermission(completion: @escaping (Bool, Error?) -> Void) {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            DispatchQueue.main.async { completion(granted, error) }
        }
    }

    func sendLocalTest(completion: @escaping (Error?) -> Void) {
        let content = UNMutableNotificationContent()
        content.title = "Свої — локальна перевірка"
        content.body = "Це тест цього iPhone. Push із сайту та фонові дзвінки ще не підключені."
        content.sound = .default
        let request = UNNotificationRequest(identifier: Self.localTestID, content: content,
                                            trigger: UNTimeIntervalNotificationTrigger(timeInterval: 2, repeats: false))
        UNUserNotificationCenter.current().add(request) { error in
            DispatchQueue.main.async { completion(error) }
        }
    }

    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                willPresent notification: UNNotification,
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.banner, .list, .sound])
    }
}
