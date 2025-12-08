# Flutter Game Container Platform - Design Document

## Overview
This document outlines the architecture for a cross-platform Flutter application that serves as a universal AI game container platform. The app will allow users to browse game rooms, join them via QR code or password, and play games through an embedded WebView component.

Key Features:
- Room list browsing
- WebView-based game loading
- QR code and password-based room joining
- Cross-platform compatibility (iOS and Android)
- Modern, responsive UI/UX

## Technical Architecture
The application will follow Flutter best practices with a clean, modular architecture:

- **Framework**: Flutter SDK (stable channel)
- **State Management**: Provider pattern
- **Navigation**: Flutter Navigator 2.0 with named routes
- **Networking**: Dio for HTTP client
- **WebView**: flutter_webview_plugin
- **QR Scanning**: qr_code_scanner
- **Local Storage**: shared_preferences
- **Build System**: Standard Flutter build system with flavors for dev/staging/prod

## Component Design

### 1. Main Application Structure
```
lib/
├── main.dart                 # Entry point
├── app.dart                  # Root application widget
├── config/                   # Configuration files
├── constants/                # Application constants
├── models/                   # Data models
├── services/                 # Business logic and API services
├── providers/                # State management providers
├── repositories/             # Data repositories
├── utils/                    # Utility functions
├── widgets/                  # Reusable UI components
└── screens/                  # Screen-specific components
    ├── home/
    ├── room_list/
    ├── room_detail/
    ├── game_view/
    ├── join_room/
    └── profile/
```

### 2. Key Components

#### MainApp (`lib/app.dart`)
- Root widget that sets up the application theme, routing, and providers
- Initializes global state and services

#### Screens
1. **HomeScreen** (`lib/screens/home/`)
   - Main dashboard with navigation to room list
   - Quick actions and user profile access

2. **RoomListScreen** (`lib/screens/room_list/`)
   - Displays scrollable list of available game rooms
   - Pull-to-refresh functionality
   - Search/filter capabilities

3. **RoomDetailScreen** (`lib/screens/room_detail/`)
   - Detailed view of a specific room
   - Join options (QR code/password)
   - Room information and status

4. **GameViewScreen** (`lib/screens/game_view/`)
   - Full-screen WebView for game rendering
   - Game controls and exit functionality

5. **JoinRoomScreen** (`lib/screens/join_room/`)
   - QR code scanner interface
   - Manual password entry form

#### Widgets
- **RoomCard**: Reusable card component for displaying room information
- **GameWebView**: Custom WebView wrapper for game loading
- **QrScanner**: QR code scanning component
- **LoadingIndicator**: Consistent loading states
- **ErrorDisplay**: Standardized error presentation

#### Services
- **ApiService**: Handles all HTTP requests to backend APIs
- **AuthService**: Manages authentication state and tokens
- **RoomService**: Business logic for room operations
- **GameService**: Game loading and lifecycle management

#### Providers
- **AuthProvider**: Authentication state
- **RoomProvider**: Room list and current room state
- **GameProvider**: Game state and WebView configuration
- **ThemeProvider**: Application theme state

## Data Models

### Room Model
```dart
class Room {
  final String id;
  final String name;
  final String description;
  final String gameUrl;
  final int playerCount;
  final int maxPlayers;
  final String status; // 'available', 'full', 'in-progress'
  final DateTime createdAt;
  final List<Player> players;
  
  // Constructor and methods...
}
```

### Player Model
```dart
class Player {
  final String id;
  final String username;
  final String avatarUrl;
  
  // Constructor and methods...
}
```

### UserModel
```dart
class User {
  final String id;
  final String username;
  final String email;
  final String avatarUrl;
  final List<String> favoriteRooms;
  
  // Constructor and methods...
}
```

## API Specifications

### Base URL
`https://api.gamecontainer.com/v1`

### Endpoints

#### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/refresh` - Token refresh

#### Rooms
- `GET /rooms` - List all rooms (with pagination)
- `GET /rooms/{id}` - Get room details
- `POST /rooms` - Create new room
- `POST /rooms/{id}/join` - Join room with password
- `GET /rooms/{id}/qr-code` - Get QR code for room

#### Users
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `GET /users/me/rooms` - Get user's rooms

### Request/Response Format
All API requests and responses use JSON format with UTF-8 encoding.

Request headers:
```
Content-Type: application/json
Authorization: Bearer <token>
```

Sample room list response:
```json
{
  "data": [
    {
      "id": "room-123",
      "name": "Chess Tournament",
      "description": "Weekly chess tournament",
      "gameUrl": "https://games.example.com/chess",
      "playerCount": 2,
      "maxPlayers": 4,
      "status": "available",
      "createdAt": "2023-05-15T10:30:00Z",
      "players": [
        {
          "id": "player-1",
          "username": "chessmaster",
          "avatarUrl": "https://avatars.example.com/player-1.jpg"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 42
  }
}
```

## Error Handling
The application implements comprehensive error handling at multiple levels:

1. **Network Errors**: Timeout, connection failures, server errors
2. **API Errors**: Invalid responses, authentication failures
3. **UI Errors**: Form validation, user input errors
4. **System Errors**: Permissions, device compatibility

Error handling strategy:
- Display user-friendly error messages
- Provide retry mechanisms where appropriate
- Log errors for debugging purposes
- Gracefully degrade functionality when possible

## Testing Strategy
The application follows a comprehensive testing approach:

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Cover edge cases and error conditions
- Target: 80%+ code coverage

### Widget Tests
- Test UI components in isolation
- Verify widget behavior and state changes
- Test user interactions

### Integration Tests
- Test complete workflows
- Verify API integrations
- Test navigation between screens

### Testing Tools
- flutter_test (built-in)
- mockito for mocking
- integration_test for integration tests

## Implementation Notes

### Cross-Platform Considerations
- Use adaptive widgets for platform-specific UI elements
- Handle iOS/Android permission differences
- Test on both platforms during development
- Consider performance differences between platforms

### Performance Optimization
- Implement lazy loading for room lists
- Cache frequently accessed data
- Optimize WebView loading
- Use const constructors where possible
- Implement proper dispose methods

### Security Considerations
- Secure storage for authentication tokens
- Validate all user inputs
- Sanitize data from APIs
- Implement proper session management

### Accessibility
- Support screen readers
- Proper contrast ratios
- Semantic labeling
- Keyboard navigation support

### Internationalization
- Support for multiple languages
- Right-to-left language support
- Date/time formatting
- Number/currency formatting