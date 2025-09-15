#if canImport(Dispatch)
import Dispatch

/// Wrapper function to replace __dispatch_queue_get_label for Linux compatibility
func getQueueLabel(_ queue: DispatchQueue?) -> String {
    #if os(macOS) || os(iOS) || os(tvOS) || os(watchOS)
    if let queue = queue {
        return String(cString: __dispatch_queue_get_label(queue))
    } else {
        return String(cString: __dispatch_queue_get_label(nil))
    }
    #else
    // On Linux, just return a placeholder string since the test is primarily for macOS
    if let queue = queue {
        return queue.label
    } else {
        return "current-queue"
    }
    #endif
}
#endif
