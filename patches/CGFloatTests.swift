#if canImport(CoreGraphics)
import CoreGraphics
import XCTest
import GRDB

class CGFloatTests: GRDBTestCase {
    
    func testCGFloat() throws {
        let dbQueue = try makeDatabaseQueue()
        try dbQueue.inDatabase { db in
            try db.execute("CREATE TABLE test(name TEXT, age REAL)")
            let value: CGFloat = 20.5
            try db.execute("INSERT INTO test(name, age) VALUES(?, ?)", arguments: ["Arthur", value])
            
            var rows = try Row.fetchAll(db, "SELECT * FROM test")
            XCTAssertEqual(rows.count, 1)
            XCTAssertEqual(rows[0]["name"] as String, "Arthur")
            XCTAssertEqual(rows[0]["age"] as Double, Double(value))
            
            rows = try Row.fetchAll(db, "SELECT * FROM test WHERE age = ?", arguments: [value])
            XCTAssertEqual(rows.count, 1)
            XCTAssertEqual(rows[0]["name"] as String, "Arthur")
            XCTAssertEqual(rows[0]["age"] as Double, Double(value))
        }
    }
}
#else
// CGFloat tests are skipped on Linux
class CGFloatTests {}
#endif