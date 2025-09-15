# GRDB.swift Docker Test Environment

This directory contains Docker configuration for building and testing GRDB.swift in a containerized environment.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

To run all tests:

```bash
docker-compose up --build grdb-swift-test
```

To run in watch mode (continuously runs tests every 30 seconds):

```bash
docker-compose --profile watch up grdb-swift-watch
```

## Test Script Options

The `run_all_tests.py` script supports various options to customize the test run:

```bash
# Run only Swift Package Manager tests
docker-compose run --rm grdb-swift-test python3 ./run_all_tests.py --package-only

# Run with code coverage enabled
docker-compose run --rm grdb-swift-test python3 ./run_all_tests.py --coverage

# Run specific tests using a filter
docker-compose run --rm grdb-swift-test python3 ./run_all_tests.py --filter "SQLite"

# Clean before building
docker-compose run --rm grdb-swift-test python3 ./run_all_tests.py --clean
```

## Test Reports

Test reports are generated in the `reports` directory, which is mounted from the container to persist results.

## Known Limitations

The containerized environment has some limitations compared to running tests on macOS:

1. Xcode-specific tests are not available (frameworks, XCFrameworks)
2. CocoaPods-based tests (SQLCipher) are not supported
3. Platform-specific tests (iOS, tvOS, watchOS) are not available

## Customizing the Environment

To modify the Swift version or add dependencies, edit the `Dockerfile` and rebuild:

```bash
docker-compose build
```