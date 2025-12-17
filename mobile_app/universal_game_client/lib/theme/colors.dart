import 'package:flutter/material.dart';

class AppColors {
  // Primary colors
  static const Color primary = Color(0xFF2196F3);
  static const Color primaryDark = Color(0xFF1976D2);
  static const Color primaryLight = Color(0xFFBBDEFB);
  
  // Secondary colors
  static const Color secondary = Color(0xFFFF9800);
  static const Color secondaryDark = Color(0xFFF57C00);
  
  // Background colors
  static const Color background = Color(0xFFF5F5F5);
  static const Color surface = Colors.white;
  static const Color darkBackground = Color(0xFF121212);
  static const Color darkSurface = Color(0xFF1E1E1E);
  
  // Text colors
  static const Color textPrimary = Color(0xFF212121);
  static const Color textSecondary = Color(0xFF757575);
  static const Color textHint = Color(0xFFBDBDBD);
  
  // Status colors
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFFFC107);
  static const Color error = Color(0xFFF44336);
  static const Color info = Color(0xFF2196F3);
  
  // Server status colors
  static const Color statusRunning = Color(0xFF4CAF50);
  static const Color statusCreating = Color(0xFFFFC107);
  static const Color statusStopped = Color(0xFF9E9E9E);
  static const Color statusError = Color(0xFFF44336);
  
  // Chip colors
  static const Color chipBackground = Color(0xFFE0E0E0);
  
  /// Returns the appropriate color for a server status
  static Color getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'running':
        return statusRunning;
      case 'creating':
        return statusCreating;
      case 'stopped':
        return statusStopped;
      case 'error':
        return statusError;
      default:
        return textSecondary;
    }
  }
}