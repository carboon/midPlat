import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import '../providers/game_server_provider.dart';
import '../services/game_server_factory_service.dart';
import '../theme/colors.dart';

/// Screen for uploading HTML game files to create a new game server.
/// Supports HTML and ZIP file selection, name/description input, and upload progress.
class UploadCodeScreen extends StatefulWidget {
  const UploadCodeScreen({super.key});

  @override
  State<UploadCodeScreen> createState() => _UploadCodeScreenState();
}

class _UploadCodeScreenState extends State<UploadCodeScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _descriptionController = TextEditingController();
  
  PlatformFile? _selectedFile;
  bool _isValidFile = false;

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['html', 'zip'],
        allowMultiple: false,
      );

      if (result != null && result.files.isNotEmpty) {
        setState(() {
          _selectedFile = result.files.first;
          _isValidFile = _validateFile(_selectedFile!);
          
          // Auto-fill name from filename if empty
          if (_nameController.text.isEmpty && _selectedFile!.name.isNotEmpty) {
            String baseName = _selectedFile!.name;
            if (baseName.toLowerCase().endsWith('.html')) {
              baseName = baseName.replaceAll('.html', '');
            } else if (baseName.toLowerCase().endsWith('.zip')) {
              baseName = baseName.replaceAll('.zip', '');
            }
            _nameController.text = baseName;
          }
        });
      }
    } catch (e) {
      _showError('Failed to pick file: $e');
    }
  }

  bool _validateFile(PlatformFile file) {
    final fileName = file.name.toLowerCase();
    
    // Check file extension
    if (!fileName.endsWith('.html') && !fileName.endsWith('.zip')) {
      _showError('Only HTML (.html) and ZIP (.zip) files are allowed');
      return false;
    }
    
    // Check file size (max 10MB for ZIP files, 1MB for HTML files)
    final maxSize = fileName.endsWith('.zip') ? 10 * 1024 * 1024 : 1024 * 1024;
    if (file.size > maxSize) {
      final maxSizeStr = fileName.endsWith('.zip') ? '10MB' : '1MB';
      _showError('File size must be less than $maxSizeStr');
      return false;
    }
    
    return true;
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.error,
      ),
    );
  }

  Future<void> _uploadCode() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedFile == null || !_isValidFile) {
      _showError('Please select a valid HTML or ZIP file');
      return;
    }

    final provider = context.read<GameServerProvider>();
    provider.setUploading(true);
    provider.clearError();

    try {
      // Get the file path
      final filePath = _selectedFile!.path;
      if (filePath == null) {
        throw NetworkException('无法获取文件路径');
      }

      final file = File(filePath);
      
      // Upload the code
      final server = await GameServerFactoryService.uploadHtmlGame(
        file: file,
        name: _nameController.text.trim(),
        description: _descriptionController.text.trim(),
        onProgress: (progress) {
          provider.setUploadProgress(progress);
        },
      );

      // Add the new server to the provider
      provider.addServer(server);
      provider.setUploading(false);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('服务器 "${server.name}" 创建成功！'),
            backgroundColor: AppColors.success,
          ),
        );
        Navigator.pop(context);
      }
    } on NetworkException catch (e) {
      provider.setUploading(false);
      provider.setError(e.message);
      _showError(e.message);
    } on ApiException catch (e) {
      provider.setUploading(false);
      provider.setError(e.message);
      _showError(e.message);
    } catch (e) {
      provider.setUploading(false);
      provider.setError('上传失败: ${e.toString()}');
      _showError('上传失败: ${e.toString()}');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Upload HTML Game'),
      ),
      body: Consumer<GameServerProvider>(
        builder: (context, provider, child) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // File picker section
                  _FilePickerSection(
                    selectedFile: _selectedFile,
                    isValidFile: _isValidFile,
                    onPickFile: _pickFile,
                  ),
                  
                  const SizedBox(height: 24),
                  
                  // Game name input
                  TextFormField(
                    controller: _nameController,
                    decoration: const InputDecoration(
                      labelText: 'Game Name',
                      hintText: 'Enter a name for your game',
                      prefixIcon: Icon(Icons.games),
                    ),
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return 'Please enter a game name';
                      }
                      if (value.length > 50) {
                        return 'Name must be less than 50 characters';
                      }
                      return null;
                    },
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // Description input
                  TextFormField(
                    controller: _descriptionController,
                    decoration: const InputDecoration(
                      labelText: 'Description (optional)',
                      hintText: 'Describe your game',
                      prefixIcon: Icon(Icons.description),
                    ),
                    maxLines: 3,
                    maxLength: 200,
                  ),
                  
                  const SizedBox(height: 24),
                  
                  // Upload progress
                  if (provider.isUploading) ...[
                    LinearProgressIndicator(value: provider.uploadProgress),
                    const SizedBox(height: 8),
                    Text(
                      'Uploading... ${(provider.uploadProgress * 100).toInt()}%',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 16),
                  ],
                  
                  // Upload button
                  ElevatedButton.icon(
                    onPressed: provider.isUploading ? null : _uploadCode,
                    icon: provider.isUploading 
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.cloud_upload),
                    label: Text(provider.isUploading ? 'Uploading...' : 'Upload & Create Server'),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // Info card
                  Card(
                    color: AppColors.info.withValues(alpha: 0.1),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.info_outline, color: AppColors.info),
                              const SizedBox(width: 8),
                              Text(
                                'Requirements',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.info,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          const Text('• HTML (.html) or ZIP (.zip) files only'),
                          const Text('• Maximum file size: 1MB for HTML, 10MB for ZIP'),
                          const Text('• Files will be analyzed for security'),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

class _FilePickerSection extends StatelessWidget {
  final PlatformFile? selectedFile;
  final bool isValidFile;
  final VoidCallback onPickFile;

  const _FilePickerSection({
    required this.selectedFile,
    required this.isValidFile,
    required this.onPickFile,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onPickFile,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          border: Border.all(
            color: selectedFile != null
                ? (isValidFile ? AppColors.success : AppColors.error)
                : AppColors.textSecondary,
            width: 2,
            style: BorderStyle.solid,
          ),
          borderRadius: BorderRadius.circular(12),
          color: selectedFile != null
              ? (isValidFile 
                  ? AppColors.success.withValues(alpha: 0.05)
                  : AppColors.error.withValues(alpha: 0.05))
              : null,
        ),
        child: Column(
          children: [
            Icon(
              selectedFile != null
                  ? (isValidFile ? Icons.check_circle : Icons.error)
                  : Icons.upload_file,
              size: 48,
              color: selectedFile != null
                  ? (isValidFile ? AppColors.success : AppColors.error)
                  : AppColors.textSecondary,
            ),
            const SizedBox(height: 12),
            Text(
              selectedFile != null
                  ? selectedFile!.name
                  : 'Tap to select HTML or ZIP file',
              style: TextStyle(
                fontSize: 16,
                fontWeight: selectedFile != null ? FontWeight.bold : FontWeight.normal,
                color: selectedFile != null
                    ? (isValidFile ? AppColors.success : AppColors.error)
                    : AppColors.textSecondary,
              ),
            ),
            if (selectedFile != null) ...[
              const SizedBox(height: 4),
              Text(
                _formatFileSize(selectedFile!.size),
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _formatFileSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
