// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "OpenWorkApp",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "OpenWorkApp", targets: ["OpenWorkApp"])
    ],
    targets: [
        .executableTarget(
            name: "OpenWorkApp",
            path: "OpenWorkApp"
        )
    ]
)
