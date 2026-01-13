import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    @State private var selectedTaskId: String?
    
    var body: some View {
        NavigationSplitView {
            SidebarView(selectedTaskId: $selectedTaskId)
        } detail: {
            if let taskId = selectedTaskId,
               let task = appState.tasks.first(where: { $0.id == taskId }) {
                TaskDetailView(task: task)
            } else {
                NewTaskView()
            }
        }
        .navigationSplitViewStyle(.balanced)
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                Button(action: { selectedTaskId = nil }) {
                    Label("New Task", systemImage: "plus")
                }
                
                Spacer()
                
                HStack {
                    Circle()
                        .fill(appState.isServerRunning ? Color.green : Color.red)
                        .frame(width: 8, height: 8)
                    Text(appState.isServerRunning ? "Server Running" : "Server Offline")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
    }
}

struct SidebarView: View {
    @EnvironmentObject var appState: AppState
    @Binding var selectedTaskId: String?
    
    var body: some View {
        List(selection: $selectedTaskId) {
            Section("Recent Tasks") {
                ForEach(appState.tasks) { task in
                    TaskRowView(task: task)
                        .tag(task.id)
                }
            }
        }
        .listStyle(.sidebar)
        .frame(minWidth: 250)
    }
}

struct TaskRowView: View {
    let task: TaskItem
    
    var body: some View {
        HStack {
            StatusIcon(status: task.status)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(task.description)
                    .lineLimit(1)
                    .font(.body)
                
                Text(task.createdAt, style: .relative)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

struct StatusIcon: View {
    let status: TaskStatus
    
    var body: some View {
        Group {
            switch status {
            case .pending:
                Image(systemName: "clock")
                    .foregroundColor(.gray)
            case .running, .thinking, .executing:
                ProgressView()
                    .scaleEffect(0.6)
            case .completed:
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
            case .failed:
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.red)
            }
        }
        .frame(width: 20)
    }
}

#Preview {
    ContentView()
        .environmentObject(AppState())
}
