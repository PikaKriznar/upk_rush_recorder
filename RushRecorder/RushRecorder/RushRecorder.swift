import Foundation
import CoreMotion
import Combine

@MainActor
final class RushRecorder: ObservableObject {

    // MARK: - Public state (UI)
    @Published var isRecording: Bool = false
    @Published var statusText: String = "Idle"
    @Published var lastPRush: Double? = nil
    @Published var lastStatus: Int? = nil
    @Published var lastHTTPStatus: Int? = nil

    // MARK: - Motion
    private let motion = CMMotionManager()

    // MARK: - Settings
    private let sampleRateHz: Double = 20.0
    private let windowDurationMs: Int64 = 5000

    /// Nastavi na IP tvojega Maca v istem omrežju (Wi-Fi):
    /// npr. http://192.168.1.45:8000/ingest
    ///
    /// - iPhone ne more dostopati do 127.0.0.1 na Macu.
    /// - Uvicorn mora poslušati na 0.0.0.0.
    private let ingestURL: URL

    // Buffer: (timestamp_ms, ax, ay, az)
    private var buffer: [(Int64, Double, Double, Double)] = []
    private var windowStartMs: Int64 = 0

    // MARK: - Init
    init(macIP: String) {
        // macIP samo "192.168.1.45" ali pa "172.20.10.3"
        self.ingestURL = URL(string: "http://172.20.10.3:8000/ingest")!

    }

    // MARK: - Control
    func start() {
        guard motion.isAccelerometerAvailable else {
            statusText = "❌ Accelerometer not available."
            return
        }

        buffer.removeAll()
        windowStartMs = nowMs()

        motion.accelerometerUpdateInterval = 1.0 / sampleRateHz

        isRecording = true
        statusText = "🎙️ Recording… (sending every 5s)"

        // .main queue je OK za demo; če bi hotela bolj smooth, lahko daš background queue
        motion.startAccelerometerUpdates(to: .main) { [weak self] data, error in
            guard let self = self else { return }

            if let error = error {
                Task { @MainActor in
                    self.statusText = "❌ Motion error: \(error.localizedDescription)"
                }
                return
            }

            guard let a = data?.acceleration else { return }

            let t = self.nowMs()
            self.buffer.append((t, a.x, a.y, a.z))

            // Pošlji na ~5 sekund
            if t - self.windowStartMs >= self.windowDurationMs {
                let csv = self.makeCSV(from: self.buffer)
                let n = self.buffer.count

                self.buffer.removeAll()
                self.windowStartMs = t

                Task { @MainActor in
                    self.statusText = "⏳ Sending \(n) samples…"
                }

                self.sendCSV(csv, samples: n)
            }
        }
    }

    func stop() {
        motion.stopAccelerometerUpdates()
        isRecording = false
        buffer.removeAll()
        statusText = "⏹️ Stopped."
    }

    // MARK: - Helpers
    private func nowMs() -> Int64 {
        Int64(Date().timeIntervalSince1970 * 1000)
    }

    private func makeCSV(from rows: [(Int64, Double, Double, Double)]) -> String {
        var s = "timestamp_ms,ax,ay,az\n"
        s.reserveCapacity(rows.count * 32)
        for (t, x, y, z) in rows {
            s += "\(t),\(x),\(y),\(z)\n"
        }
        return s
    }

    // MARK: - Networking
    private func sendCSV(_ csv: String, samples: Int) {
        var req = URLRequest(url: ingestURL)
        req.httpMethod = "POST"
        req.setValue("text/csv", forHTTPHeaderField: "Content-Type")
        req.httpBody = csv.data(using: .utf8)
        req.timeoutInterval = 6.0  // okno je 5s, daj malo rezerve

        URLSession.shared.dataTask(with: req) { [weak self] data, resp, err in
            guard let self = self else { return }

            Task { @MainActor in
                if let http = resp as? HTTPURLResponse {
                    self.lastHTTPStatus = http.statusCode
                    print("HTTP status:", http.statusCode)
                } else {
                    self.lastHTTPStatus = nil
                }

                if let err = err {
                    self.statusText = "❌ Send failed: \(err.localizedDescription)"
                    return
                }

                let bodyString: String = {
                    guard let data = data, let s = String(data: data, encoding: .utf8) else { return "" }
                    return s
                }()

                if !bodyString.isEmpty {
                    print("Response body:", bodyString)
                }

                // Poskusi JSON parse: {"p_rush": 0.87, "status": 1}
                if let data = data,
                   let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {

                    // JSON lahko vrne številke kot Double ali kot NSNumber
                    let p = (json["p_rush"] as? Double) ?? (json["p_rush"] as? NSNumber)?.doubleValue
                    let st = (json["status"] as? Int) ?? (json["status"] as? NSNumber)?.intValue

                    if let p = p, let st = st {
                        self.lastPRush = p
                        self.lastStatus = st

                        let state = (st == 1) ? "🚨 RUSH" : "✅ CALM"
                        self.statusText = "✅ Sent \(samples) → p_rush=\(String(format: "%.2f", p)) \(state)"
                        return
                    }
                }

                // Fallback, če JSON ni prav
                if let http = resp as? HTTPURLResponse {
                    self.statusText = "⚠️ Sent \(samples). HTTP \(http.statusCode)."
                } else {
                    self.statusText = "⚠️ Sent \(samples)."
                }
            }
        }.resume()
    }
}
