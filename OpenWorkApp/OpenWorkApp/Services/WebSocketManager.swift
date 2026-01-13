import Foundation

class WebSocketManager: NSObject {
    private var webSocket: URLSessionWebSocketTask?
    private var session: URLSession!
    private var messageHandler: (([String: Any]) -> Void)?
    private let url: URL
    private var isConnected = false
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 5
    
    init(url: URL = URL(string: "ws://127.0.0.1:8765/ws")!) {
        self.url = url
        super.init()
        self.session = URLSession(configuration: .default, delegate: self, delegateQueue: OperationQueue())
    }
    
    func connect(onMessage: @escaping ([String: Any]) -> Void) {
        self.messageHandler = onMessage
        connectWebSocket()
    }
    
    private func connectWebSocket() {
        webSocket = session.webSocketTask(with: url)
        webSocket?.resume()
        isConnected = true
        reconnectAttempts = 0
        receiveMessage()
    }
    
    func disconnect() {
        isConnected = false
        webSocket?.cancel(with: .normalClosure, reason: nil)
        webSocket = nil
    }
    
    private func receiveMessage() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self?.handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        self?.handleMessage(text)
                    }
                @unknown default:
                    break
                }
                // Continue receiving
                self?.receiveMessage()
                
            case .failure(let error):
                print("WebSocket receive error: \(error)")
                self?.handleDisconnect()
            }
        }
    }
    
    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return
        }
        messageHandler?(json)
    }
    
    private func handleDisconnect() {
        isConnected = false
        
        // Attempt to reconnect
        guard reconnectAttempts < maxReconnectAttempts else {
            print("Max reconnect attempts reached")
            return
        }
        
        reconnectAttempts += 1
        let delay = Double(reconnectAttempts) * 2.0 // Exponential backoff
        
        DispatchQueue.main.asyncAfter(deadline: .now() + delay) { [weak self] in
            print("Attempting to reconnect (\(self?.reconnectAttempts ?? 0)/\(self?.maxReconnectAttempts ?? 5))")
            self?.connectWebSocket()
        }
    }
    
    func send(_ message: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: message),
              let text = String(data: data, encoding: .utf8) else {
            return
        }
        
        webSocket?.send(.string(text)) { error in
            if let error = error {
                print("WebSocket send error: \(error)")
            }
        }
    }
}

extension WebSocketManager: URLSessionWebSocketDelegate {
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        print("WebSocket connected")
        isConnected = true
    }
    
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        print("WebSocket disconnected")
        isConnected = false
        handleDisconnect()
    }
}
