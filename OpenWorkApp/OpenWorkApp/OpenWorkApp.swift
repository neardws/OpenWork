import SwiftUI

@main
struct OpenWorkApp: App {
    @StateObject private var appState = AppState()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .frame(minWidth: 800, minHeight: 600)
        }
        .windowStyle(.hiddenTitleBar)
        .commands {
            CommandGroup(replacing: .newItem) {
                Button("New Task") {
                    appState.showNewTask = true
                }
                .keyboardShortcut("n", modifiers: .command)
            }
        }
        
        Settings {
            SettingsView()
                .environmentObject(appState)
        }
    }
}

class AppState: ObservableObject {
    @Published var isServerRunning = false
    @Published var showNewTask = false
    @Published var selectedModel = "gpt-4"
    @Published var apiKey = ""
    @Published var tasks: [TaskItem] = []
    @Published var currentTask: TaskItem?
    
    private var serverProcess: Process?
    private let apiClient = APIClient()
    private let webSocketManager = WebSocketManager()
    
    init() {
        loadSettings()
        startServer()
        connectWebSocket()
    }
    
    func loadSettings() {
        apiKey = UserDefaults.standard.string(forKey: "apiKey") ?? ""
        selectedModel = UserDefaults.standard.string(forKey: "selectedModel") ?? "gpt-4"
    }
    
    func saveSettings() {
        UserDefaults.standard.set(apiKey, forKey: "apiKey")
        UserDefaults.standard.set(selectedModel, forKey: "selectedModel")
    }
    
    func startServer() {
        // Find Python and start the server
        let pythonPath = findPythonPath()
        guard let python = pythonPath else {
            print("Python not found")
            return
        }
        
        serverProcess = Process()
        serverProcess?.executableURL = URL(fileURLWithPath: python)
        serverProcess?.arguments = ["-m", "openwork.server.app"]
        
        do {
            try serverProcess?.run()
            isServerRunning = true
            print("Server started")
        } catch {
            print("Failed to start server: \(error)")
        }
    }
    
    func stopServer() {
        serverProcess?.terminate()
        isServerRunning = false
    }
    
    func connectWebSocket() {
        webSocketManager.connect { [weak self] message in
            DispatchQueue.main.async {
                self?.handleWebSocketMessage(message)
            }
        }
    }
    
    func handleWebSocketMessage(_ message: [String: Any]) {
        guard let taskId = message["task_id"] as? String,
              let event = message["event"] as? String else { return }
        
        if let index = tasks.firstIndex(where: { $0.id == taskId }) {
            switch event {
            case "thinking":
                tasks[index].status = .thinking
            case "executing":
                tasks[index].status = .executing
                if let data = message["data"] as? [String: Any],
                   let tool = data["tool"] as? String {
                    tasks[index].currentTool = tool
                }
            case "finished":
                if let data = message["data"] as? [String: Any] {
                    tasks[index].status = data["status"] as? String == "completed" ? .completed : .failed
                    tasks[index].output = data["output"] as? String
                    tasks[index].error = data["error"] as? String
                }
            case "error":
                tasks[index].status = .failed
                if let data = message["data"] as? [String: Any] {
                    tasks[index].error = data["error"] as? String
                }
            default:
                break
            }
        }
    }
    
    func submitTask(description: String, allowedPaths: [String]) {
        let task = TaskItem(
            id: UUID().uuidString,
            description: description,
            allowedPaths: allowedPaths,
            status: .pending
        )
        tasks.insert(task, at: 0)
        currentTask = task
        
        apiClient.createTask(
            task: description,
            allowedPaths: allowedPaths,
            model: selectedModel,
            apiKey: apiKey
        ) { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success(let response):
                    if let index = self?.tasks.firstIndex(where: { $0.id == task.id }) {
                        self?.tasks[index].id = response.taskId
                        self?.tasks[index].status = .running
                    }
                case .failure(let error):
                    if let index = self?.tasks.firstIndex(where: { $0.id == task.id }) {
                        self?.tasks[index].status = .failed
                        self?.tasks[index].error = error.localizedDescription
                    }
                }
            }
        }
    }
    
    private func findPythonPath() -> String? {
        let paths = [
            "/usr/local/bin/python3",
            "/opt/homebrew/bin/python3",
            "/usr/bin/python3",
        ]
        for path in paths {
            if FileManager.default.fileExists(atPath: path) {
                return path
            }
        }
        return nil
    }
    
    deinit {
        stopServer()
    }
}
