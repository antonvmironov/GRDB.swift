// swift-tools-version:6.0
// The swift-tools-version declares the minimum version of Swift required to build this package.

import Foundation
import PackageDescription

var swiftSettings: [SwiftSetting] = [
    .define("SQLITE_ENABLE_FTS5"),
]
var cSettings: [CSetting] = []
var dependencies: [PackageDescription.Package.Dependency] = []

// Don't rely on those environment variables. They are ONLY testing conveniences:
// $ SQLITE_ENABLE_PREUPDATE_HOOK=1 make test_SPM
if ProcessInfo.processInfo.environment["SQLITE_ENABLE_PREUPDATE_HOOK"] == "1" {
    swiftSettings.append(.define("SQLITE_ENABLE_PREUPDATE_HOOK"))
    cSettings.append(.define("GRDB_SQLITE_ENABLE_PREUPDATE_HOOK"))
}

// The SPI_BUILDER environment variable enables documentation building
// on <https://swiftpackageindex.com/groue/GRDB.swift>. See
// <https://github.com/SwiftPackageIndex/SwiftPackageIndex-Server/issues/2122>
// for more information.
//
// SPI_BUILDER also enables the `make docs-localhost` command.
if ProcessInfo.processInfo.environment["SPI_BUILDER"] == "1" {
    dependencies.append(.package(url: "https://github.com/apple/swift-docc-plugin", from: "1.0.0"))
}

let package = Package(
    name: "GRDB",
    defaultLocalization: "en", // for tests
    platforms: [
        .iOS(.v13),
        .macOS(.v10_15),
        .tvOS(.v13),
        .watchOS(.v7),
    ],
    products: [
        .library(name: "GRDBSQLite", targets: ["GRDBSQLite"]),
        .library(name: "GRDB", targets: ["GRDB"]),
        .library(name: "GRDB-dynamic", type: .dynamic, targets: ["GRDB"]),
    ],
    dependencies: dependencies,
    targets: [
        .target(
            name: "GRDBSQLite",
            publicHeadersPath: ".",
            cSettings: [
                .define("SQLITE_DEFAULT_MEMSTATUS", to: "0"),
                .define("SQLITE_ENABLE_FTS5", to: "1"),
                .define("SQLITE_ENABLE_JSON1", to: "1"),
                .define("SQLITE_ENABLE_SNAPSHOT", to: "1"),
                .define("SQLITE_OMIT_DEPRECATED", to: "1"),
                .define("SQLITE_THREADSAFE", to: "1"),
                .define("SQLITE_ENABLE_PREUPDATE_HOOK", to: "1"),
                .define("SQLITE_ENABLE_SESSION", to: "1"),
                .define("SQLITE_ENABLE_RTREE", to: "1"),
                .define("SQLITE_ENABLE_COLUMN_METADATA", to: "1"),
                .define("SQLITE_SECURE_DELETE", to: "1"),
                .define("SQLITE_SOUNDEX", to: "1"),
                .define("SQLITE_USE_ALLOCA", to: "1"),
                .define("SQLITE_EXTRA_AUTOEXT", to: "sqlite3_uuid_init,sqlite3_vec_init"),
                .define("SQLITE_VEC_STATIC", to: "1"),
                ],
            linkerSettings: [
                .linkedLibrary("pthread", .when(platforms: [.linux])),
                .linkedLibrary("dl",      .when(platforms: [.linux])),
            ]
        ),
        .target(
            name: "GRDB",
            dependencies: ["GRDBSQLite"],
            path: "GRDB",
            resources: [.copy("PrivacyInfo.xcprivacy")],
            cSettings: cSettings,
            swiftSettings: swiftSettings),
        .testTarget(
            name: "GRDBTests",
            dependencies: ["GRDB"],
            path: "Tests",
            exclude: [
                "CocoaPods",
                "Crash",
                "CustomSQLite",
                "GRDBManualInstall",
                "GRDBTests/getThreadsCount.c",
                "Info.plist",
                "Performance",
                "SPM",
                "Swift6Migration",
                "generatePerformanceReport.rb",
                "parsePerformanceTests.rb",
            ],
            resources: [
                .copy("GRDBTests/Betty.jpeg"),
                .copy("GRDBTests/InflectionsTests.json"),
                .copy("GRDBTests/Issue1383.sqlite"),
            ],
            cSettings: cSettings,
            swiftSettings: swiftSettings + [
                // Tests still use the Swift 5 language mode.
                .swiftLanguageMode(.v5),
                .enableUpcomingFeature("InferSendableFromCaptures"),
                .enableUpcomingFeature("GlobalActorIsolatedTypesUsability"),
            ])
    ],
    swiftLanguageModes: [.v6]
)
