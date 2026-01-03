import SwiftUI

struct ContentView: View {
    @StateObject private var rec = RushRecorder(macIP: "192.168.1.45") // <-- TU vpiši IP Maca

    @State private var pulse = false

    var body: some View {
        VStack(spacing: 18) {

            // Header
            VStack(spacing: 6) {
                Text("Rush Index — Live Demo")
                    .font(.title2)
                    .bold()

                HStack(spacing: 8) {
                    Circle()
                        .fill(rec.isRecording ? Color.red : Color.gray)
                        .frame(width: 10, height: 10)
                        .scaleEffect(rec.isRecording && pulse ? 1.6 : 1.0)
                        .opacity(rec.isRecording && pulse ? 0.5 : 1.0)
                        .animation(rec.isRecording ? .easeInOut(duration: 0.8).repeatForever(autoreverses: true) : .default,
                                   value: pulse)

                    Text(rec.isRecording ? "RUNNING" : "IDLE")
                        .font(.caption)
                        .bold()
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background((rec.isRecording ? Color.red : Color.gray).opacity(0.15))
                        .foregroundStyle(rec.isRecording ? .red : .gray)
                        .clipShape(Capsule())
                }
            }
            .padding(.top, 6)

            // Status card
            VStack(alignment: .leading, spacing: 10) {
                HStack(alignment: .center, spacing: 10) {
                    Image(systemName: rec.isRecording ? "waveform" : "checkmark.seal")
                        .font(.title3)

                    Text(rec.statusText)
                        .font(.headline)
                        .multilineTextAlignment(.leading)

                    Spacer()

                    if rec.isRecording {
                        ProgressView()
                            .scaleEffect(1.05)
                    }
                }

                Divider().opacity(0.5)

                HStack {
                    if let http = rec.lastHTTPStatus {
                        Label("HTTP: \(http)", systemImage: "network")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    } else {
                        Label("HTTP: —", systemImage: "network")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                }

                if let p = rec.lastPRush, let st = rec.lastStatus {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack {
                            Text("p_rush: \(String(format: "%.2f", p))")
                                .font(.subheadline)
                                .bold()
                            Spacer()
                            Text("q/status: \(st)")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }

                        // preprost vizualni indikator verjetnosti
                        ProgressView(value: min(max(p, 0.0), 1.0))
                            .animation(.easeInOut(duration: 0.25), value: p)
                    }
                } else {
                    Text("Ni dovolj podatkov še — klikni Start in počakaj ~5 s.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(14)
            .background(.thinMaterial)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(Color.primary.opacity(0.07), lineWidth: 1)
            )

            // Buttons
            HStack(spacing: 12) {
                Button {
                    rec.start()
                } label: {
                    HStack(spacing: 10) {
                        Image(systemName: "play.fill")
                        Text("Start")
                            .bold()
                    }
                    .frame(maxWidth: .infinity, minHeight: 54)
                }
                .buttonStyle(.borderedProminent)
                .tint(.green)
                .disabled(rec.isRecording)

                Button {
                    rec.stop()
                } label: {
                    HStack(spacing: 10) {
                        Image(systemName: "stop.fill")
                        Text("Stop")
                            .bold()
                    }
                    .frame(maxWidth: .infinity, minHeight: 54)
                }
                .buttonStyle(.borderedProminent)
                .tint(.red)
                .disabled(!rec.isRecording)
            }

            Spacer(minLength: 0)
        }
        .padding()
        .onAppear {
            // sproži animacijo pulza (vezana na isRecording)
            pulse = true
        }
    }
}
