import Foundation

enum TaskStatus: String, Codable {
    case pending
    case running
    case thinking
    case executing
    case completed
    case failed
}

struct TaskItem: Identifiable, Codable {
    var id: String
    var description: String
    var allowedPaths: [String]
    var status: TaskStatus
    var output: String?
    var error: String?
    var currentTool: String?
    var toolLogs: [ToolLog] = []
    var createdAt: Date = Date()
    
    init(
        id: String = UUID().uuidString,
        description: String,
        allowedPaths: [String],
        status: TaskStatus = .pending,
        output: String? = nil,
        error: String? = nil
    ) {
        self.id = id
        self.description = description
        self.allowedPaths = allowedPaths
        self.status = status
        self.output = output
        self.error = error
    }
}

struct ToolLog: Identifiable, Codable {
    let id: String
    let toolName: String
    let success: Bool
    let output: String?
    let error: String?
    let timestamp: Date
    
    init(
        id: String = UUID().uuidString,
        toolName: String,
        success: Bool,
        output: String? = nil,
        error: String? = nil,
        timestamp: Date = Date()
    ) {
        self.id = id
        self.toolName = toolName
        self.success = success
        self.output = output
        self.error = error
        self.timestamp = timestamp
    }
}

struct TaskResponse: Codable {
    let taskId: String
    let status: String
    let output: String?
    let error: String?
    let iterations: Int?
    
    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case status
        case output
        case error
        case iterations
    }
}
