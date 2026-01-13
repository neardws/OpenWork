# OpenWork macOS App

Native macOS application for OpenWork - an open source AI agent for local file automation.

## Requirements

- macOS 13.0 (Ventura) or later
- Xcode 15.0 or later
- Python 3.10+ (for backend)

## Building

### Option 1: Using Xcode

1. Open `OpenWorkApp.xcodeproj` in Xcode
2. Select your team for code signing
3. Build and run (⌘R)

### Option 2: Using Swift Package Manager

```bash
cd OpenWorkApp
swift build
swift run
```

## Architecture

```
┌─────────────────────────────┐
│   SwiftUI macOS App         │
│   - Task input & management │
│   - Real-time progress      │
│   - Native folder picker    │
└──────────────┬──────────────┘
               │ HTTP/WebSocket
               │ (localhost:8765)
┌──────────────▼──────────────┐
│   OpenWork Python Backend   │
│   (FastAPI Server)          │
└─────────────────────────────┘
```

## Features

- **Native macOS UI**: Built with SwiftUI for a seamless Mac experience
- **Task Management**: Create, monitor, and manage automation tasks
- **Real-time Updates**: WebSocket connection for live progress updates
- **Folder Authorization**: Native folder picker with drag & drop support
- **Model Selection**: Choose from multiple LLM providers
- **Dark Mode**: Full support for macOS dark mode

## Project Structure

```
OpenWorkApp/
├── OpenWorkApp.swift       # App entry point
├── ContentView.swift       # Main window layout
├── Views/
│   ├── NewTaskView.swift   # Task creation interface
│   ├── TaskDetailView.swift # Task progress & results
│   └── SettingsView.swift  # App settings
├── Models/
│   └── Task.swift          # Data models
├── Services/
│   ├── APIClient.swift     # HTTP API client
│   └── WebSocketManager.swift # WebSocket client
└── Resources/
    └── Assets.xcassets     # App icons & images
```

## Backend Setup

The macOS app requires the OpenWork Python backend to be running:

```bash
# Option 1: The app starts the server automatically

# Option 2: Start manually
cd /path/to/OpenWork
pip install -e .
openwork serve
```

## Configuration

Settings are stored in UserDefaults:

- **API Key**: Your LLM provider API key
- **Default Model**: Preferred model for new tasks
- **Server Host/Port**: Backend server location

## Keyboard Shortcuts

- `⌘N` - New Task
- `⌘,` - Open Settings
- `⌘Enter` - Start Task
- `⌘Q` - Quit

## License

MIT License - see [LICENSE](../LICENSE) for details.
