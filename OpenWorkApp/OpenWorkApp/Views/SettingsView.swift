import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var appState: AppState
    @State private var apiKey = ""
    @State private var selectedModel = "gpt-4"
    @State private var serverHost = "127.0.0.1"
    @State private var serverPort = "8765"
    
    var body: some View {
        TabView {
            // API Settings
            Form {
                Section("API Configuration") {
                    SecureField("API Key", text: $apiKey)
                        .textFieldStyle(.roundedBorder)
                    
                    Text("Enter your OpenAI, Anthropic, or other provider API key")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Picker("Default Model", selection: $selectedModel) {
                        Section("OpenAI") {
                            Text("GPT-4").tag("gpt-4")
                            Text("GPT-3.5 Turbo").tag("gpt-3.5-turbo")
                        }
                        Section("Anthropic") {
                            Text("Claude Sonnet").tag("claude-sonnet")
                            Text("Claude Haiku").tag("claude-haiku")
                        }
                        Section("Google") {
                            Text("Gemini Pro").tag("gemini")
                        }
                        Section("Local (Ollama)") {
                            Text("Llama 2").tag("ollama/llama2")
                            Text("Mistral").tag("ollama/mistral")
                        }
                    }
                }
                
                Section {
                    Button("Save") {
                        saveAPISettings()
                    }
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding()
            .tabItem {
                Label("API", systemImage: "key")
            }
            
            // Server Settings
            Form {
                Section("Server Configuration") {
                    TextField("Host", text: $serverHost)
                        .textFieldStyle(.roundedBorder)
                    
                    TextField("Port", text: $serverPort)
                        .textFieldStyle(.roundedBorder)
                    
                    HStack {
                        Circle()
                            .fill(appState.isServerRunning ? Color.green : Color.red)
                            .frame(width: 10, height: 10)
                        Text(appState.isServerRunning ? "Server Running" : "Server Offline")
                    }
                }
                
                Section {
                    HStack {
                        Button("Restart Server") {
                            restartServer()
                        }
                        
                        Button("Stop Server") {
                            appState.stopServer()
                        }
                        .disabled(!appState.isServerRunning)
                    }
                }
            }
            .padding()
            .tabItem {
                Label("Server", systemImage: "server.rack")
            }
            
            // About
            VStack(spacing: 20) {
                Image(systemName: "cpu")
                    .font(.system(size: 64))
                    .foregroundColor(.accentColor)
                
                Text("OpenWork")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Version 0.1.0")
                    .foregroundColor(.secondary)
                
                Text("Open source AI agent for local file automation")
                    .multilineTextAlignment(.center)
                    .foregroundColor(.secondary)
                
                Divider()
                    .frame(width: 200)
                
                Link("View on GitHub", destination: URL(string: "https://github.com/neardws/OpenWork")!)
                
                Text("Inspired by Claude Cowork")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .tabItem {
                Label("About", systemImage: "info.circle")
            }
        }
        .frame(width: 450, height: 350)
        .onAppear {
            loadSettings()
        }
    }
    
    private func loadSettings() {
        apiKey = appState.apiKey
        selectedModel = appState.selectedModel
    }
    
    private func saveAPISettings() {
        appState.apiKey = apiKey
        appState.selectedModel = selectedModel
        appState.saveSettings()
    }
    
    private func restartServer() {
        appState.stopServer()
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            appState.startServer()
        }
    }
}

#Preview {
    SettingsView()
        .environmentObject(AppState())
}
