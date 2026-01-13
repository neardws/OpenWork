import SwiftUI

struct TaskDetailView: View {
    let task: TaskItem
    @State private var showLogs = true
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        StatusBadge(status: task.status)
                        Text(task.createdAt, style: .relative)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    Text(task.description)
                        .font(.title2)
                        .fontWeight(.semibold)
                        .lineLimit(3)
                }
                
                Spacer()
                
                if task.status == .running || task.status == .thinking || task.status == .executing {
                    Button("Cancel") {
                        // TODO: Implement cancel
                    }
                    .buttonStyle(.bordered)
                }
            }
            .padding()
            
            Divider()
            
            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Status Section
                    if task.status == .running || task.status == .thinking || task.status == .executing {
                        RunningStatusView(task: task)
                    }
                    
                    // Output Section
                    if let output = task.output, !output.isEmpty {
                        OutputSection(title: "Result", content: output, isSuccess: true)
                    }
                    
                    // Error Section
                    if let error = task.error, !error.isEmpty {
                        OutputSection(title: "Error", content: error, isSuccess: false)
                    }
                    
                    // Allowed Paths
                    if !task.allowedPaths.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Allowed Folders")
                                .font(.headline)
                            
                            ForEach(task.allowedPaths, id: \.self) { path in
                                HStack {
                                    Image(systemName: "folder.fill")
                                        .foregroundColor(.accentColor)
                                    Text(path)
                                        .font(.system(.body, design: .monospaced))
                                        .lineLimit(1)
                                        .truncationMode(.middle)
                                }
                            }
                        }
                        .padding()
                        .background(Color(NSColor.controlBackgroundColor))
                        .cornerRadius(8)
                    }
                    
                    // Tool Logs
                    if !task.toolLogs.isEmpty {
                        DisclosureGroup(isExpanded: $showLogs) {
                            VStack(alignment: .leading, spacing: 8) {
                                ForEach(task.toolLogs) { log in
                                    ToolLogRow(log: log)
                                }
                            }
                        } label: {
                            HStack {
                                Image(systemName: "terminal")
                                Text("Tool Executions (\(task.toolLogs.count))")
                                    .font(.headline)
                            }
                        }
                        .padding()
                        .background(Color(NSColor.controlBackgroundColor))
                        .cornerRadius(8)
                    }
                }
                .padding()
            }
        }
    }
}

struct StatusBadge: View {
    let status: TaskStatus
    
    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)
            Text(statusText)
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(statusColor.opacity(0.15))
        .cornerRadius(4)
    }
    
    var statusColor: Color {
        switch status {
        case .pending: return .gray
        case .running, .thinking, .executing: return .blue
        case .completed: return .green
        case .failed: return .red
        }
    }
    
    var statusText: String {
        switch status {
        case .pending: return "Pending"
        case .running: return "Running"
        case .thinking: return "Thinking"
        case .executing: return "Executing"
        case .completed: return "Completed"
        case .failed: return "Failed"
        }
    }
}

struct RunningStatusView: View {
    let task: TaskItem
    
    var body: some View {
        HStack(spacing: 16) {
            ProgressView()
            
            VStack(alignment: .leading, spacing: 4) {
                Text(statusMessage)
                    .font(.headline)
                
                if let tool = task.currentTool {
                    Text("Using: \(tool)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
        }
        .padding()
        .background(Color.blue.opacity(0.1))
        .cornerRadius(8)
    }
    
    var statusMessage: String {
        switch task.status {
        case .thinking: return "Thinking about the task..."
        case .executing: return "Executing tool..."
        default: return "Working on task..."
        }
    }
}

struct OutputSection: View {
    let title: String
    let content: String
    let isSuccess: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: isSuccess ? "checkmark.circle.fill" : "xmark.circle.fill")
                    .foregroundColor(isSuccess ? .green : .red)
                Text(title)
                    .font(.headline)
            }
            
            Text(content)
                .font(.body)
                .textSelection(.enabled)
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color(NSColor.textBackgroundColor))
                .cornerRadius(6)
        }
        .padding()
        .background(Color(NSColor.controlBackgroundColor))
        .cornerRadius(8)
    }
}

struct ToolLogRow: View {
    let log: ToolLog
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Image(systemName: log.success ? "checkmark.circle" : "xmark.circle")
                    .foregroundColor(log.success ? .green : .red)
                Text(log.toolName)
                    .fontWeight(.medium)
                Spacer()
                Text(log.timestamp, style: .time)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if let output = log.output {
                Text(output)
                    .font(.system(.caption, design: .monospaced))
                    .lineLimit(3)
                    .foregroundColor(.secondary)
            }
        }
        .padding(8)
        .background(Color(NSColor.textBackgroundColor))
        .cornerRadius(4)
    }
}

#Preview {
    TaskDetailView(task: TaskItem(
        id: "1",
        description: "Organize my downloads folder by file type and create a summary",
        allowedPaths: ["/Users/test/Downloads"],
        status: .completed,
        output: "Successfully organized 42 files into 5 categories."
    ))
    .frame(width: 600, height: 700)
}
