import Foundation
// Resize the existing logo using Apple's command-line image converter.
// An opaque JPEG intermediary avoids unsupported 24-bit AppKit drawing contexts.
guard CommandLine.arguments.count == 3 else {
    print("Usage: prepare-icon.swift existing-logo output.png")
    exit(2)
}
let input = URL(fileURLWithPath: CommandLine.arguments[1]).standardizedFileURL
let output = URL(fileURLWithPath: CommandLine.arguments[2]).standardizedFileURL
let intermediate = output.deletingLastPathComponent().appendingPathComponent("AppIcon-intermediate.jpg")
func convert(_ arguments: [String]) throws {
    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/sips")
    process.arguments = arguments
    try process.run()
    process.waitUntilExit()
    guard process.terminationStatus == 0 else {
        throw NSError(domain: "Svoyi.IconConversion", code: Int(process.terminationStatus))
    }
}
do {
    guard FileManager.default.fileExists(atPath: input.path) else {
        throw NSError(domain: "Svoyi.MissingIcon", code: 1)
    }
    try FileManager.default.createDirectory(at: output.deletingLastPathComponent(), withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: intermediate) }
    try convert(["-z", "1024", "1024", "-s", "format", "jpeg", "-s", "formatOptions", "best", input.path, "--out", intermediate.path])
    try convert(["-s", "format", "png", intermediate.path, "--out", output.path])
    print("Existing logo converted; validate.py will verify RGB format and dimensions")
} catch {
    print("Icon conversion failed: \(error)")
    exit(1)
}
