import SwiftUI
import UniformTypeIdentifiers

struct NewTaskView: View {
    @EnvironmentObject var appState: AppState
    @State private var taskDescription = ""
    @State private var allowedPaths: [String] = []
    @State private var isTargeted = false
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading) {
                    Text("New Task")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    Text("Describe what you want OpenWork to do")
                        .foregroundColor(.secondary)
                }
                Spacer()
            }
            .padding()
            
            Divider()
            
            // Content
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Task Input
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Task Description", systemImage: "text.alignleft")
                            .font(.headline)
                        
                        TextEditor(text: $taskDescription)
                            .font(.body)
                            .frame(minHeight: 120)
                            .padding(8)
                            .background(Color(NSColor.textBackgroundColor))
                            .cornerRadius(8)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                            )
                        
                        Text("Example: \"Organize my downloads folder by file type\" or \"Find all PDF files and create a summary\"")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    // Model Selection
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Model", systemImage: "cpu")
                            .font(.headline)
                        
                        Picker("", selection: $appState.selectedModel) {
                            Text("GPT-4").tag("gpt-4")
                            Text("GPT-3.5 Turbo").tag("gpt-3.5-turbo")
                            Text("Claude Sonnet").tag("claude-sonnet")
                            Text("Claude Haiku").tag("claude-haiku")
                            Text("Gemini Pro").tag("gemini")
                            Divider()
                            Text("Llama 2 (Local)").tag("ollama/llama2")
                            Text("Mistral (Local)").tag("ollama/mistral")
                        }
                        .pickerStyle(.menu)
                        .frame(width: 200)
                    }
                    
                    // Allowed Paths
                    VStack(alignment: .leading, spacing: 8) {
                        Label("Allowed Folders", systemImage: "folder")
                            .font(.headline)
                        
                        Text("OpenWork can only access files in these folders")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        
                        // Drop zone
                        ZStack {
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(style: StrokeStyle(lineWidth: 2, dash: [8]))
                                .foregroundColor(isTargeted ? .accentColor : .gray.opacity(0.5))
                                .background(
                                    RoundedRectangle(cornerRadius: 8)
                                        .fill(isTargeted ? Color.accentColor.opacity(0.1) : Color.clear)
                                )
                            
                            VStack(spacing: 8) {
                                Image(systemName: "folder.badge.plus")
                                    .font(.largeTitle)
                                    .foregroundColor(.secondary)
                                Text("Drop folders here or click to browse")
                                    .foregroundColor(.secondary)
                            }
                        }
                        .frame(height: 100)
                        .onTapGesture {
                            selectFolder()
                        }
                        .onDrop(of: [UTType.fileURL], isTargeted: $isTargeted) { providers in
                            handleDrop(providers: providers)
                            return true
                        }
                        
                        // Path list
                        if !allowedPaths.isEmpty {
                            VStack(spacing: 4) {
                                ForEach(allowedPaths, id: \.self) { path in
                                    HStack {
                                        Image(systemName: "folder.fill")
                                            .foregroundColor(.accentColor)
                                        Text(path)
                                            .lineLimit(1)
                                            .truncationMode(.middle)
                                        Spacer()
                                        Button(action: {
                                            allowedPaths.removeAll { $0 == path }
                                        }) {
                                            Image(systemName: "xmark.circle.fill")
                                                .foregroundColor(.secondary)
                                        }
                                        .buttonStyle(.plain)
                                    }
                                    .padding(8)
                                    .background(Color(NSColor.controlBackgroundColor))
                                    .cornerRadius(6)
                                }
                            }
                        }
                    }
                }
                .padding()
            }
            
            Divider()
            
            // Footer
            HStack {
                if appState.apiKey.isEmpty {
                    Label("API key not set", systemImage: "exclamationmark.triangle")
                        .foregroundColor(.orange)
                        .font(.caption)
                }
                
                Spacer()
                
                Button("Start Task") {
                    submitTask()
                }
                .buttonStyle(.borderedProminent)
                .disabled(taskDescription.isEmpty || allowedPaths.isEmpty || appState.apiKey.isEmpty)
                .keyboardShortcut(.return, modifiers: .command)
            }
            .padding()
        }
    }
    
    private func selectFolder() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = true
        
        if panel.runModal() == .OK {
            for url in panel.urls {
                let path = url.path
                if !allowedPaths.contains(path) {
                    allowedPaths.append(path)
                }
            }
        }
    }
    
    private func handleDrop(providers: [NSItemProvider]) {
        for provider in providers {
            provider.loadItem(forTypeIdentifier: UTType.fileURL.identifier, options: nil) { item, error in
                guard let data = item as? Data,
                      let url = URL(dataRepresentation: data, relativeTo: nil) else { return }
                
                var isDirectory: ObjCBool = false
                if FileManager.default.fileExists(atPath: url.path, isDirectory: &isDirectory),
                   isDirectory.boolValue {
                    DispatchQueue.main.async {
                        if !allowedPaths.contains(url.path) {
                            allowedPaths.append(url.path)
                        }
                    }
                }
            }
        }
    }
    
    private func submitTask() {
        appState.submitTask(description: taskDescription, allowedPaths: allowedPaths)
        taskDescription = ""
    }
}

#Preview {
    NewTaskView()
        .environmentObject(AppState())
        .frame(width: 600, height: 700)
}
