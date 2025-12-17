import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/game_server_provider.dart';
import '../models/game_server_instance.dart';
import '../services/game_server_factory_service.dart';
import '../theme/colors.dart';

/// Screen displaying detailed information about a game server instance.
/// Shows status, resource usage, logs, and lifecycle management controls.
class ServerDetailScreen extends StatefulWidget {
  const ServerDetailScreen({super.key});

  @override
  State<ServerDetailScreen> createState() => _ServerDetailScreenState();
}

class _ServerDetailScreenState extends State<ServerDetailScreen> {
  bool _isLoading = false;

  Future<void> _refreshServer() async {
    final provider = context.read<GameServerProvider>();
    final server = provider.currentServer;
    if (server == null) return;

    setState(() => _isLoading = true);
    try {
      final updatedServer = await GameServerFactoryService.fetchServerDetails(server.serverId);
      provider.updateServer(updatedServer);
      provider.setCurrentServer(updatedServer);
    } on NetworkException catch (e) {
      _showError(e.message);
    } on ApiException catch (e) {
      _showError(e.message);
    } catch (e) {
      _showError('刷新失败: ${e.toString()}');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _stopServer() async {
    final provider = context.read<GameServerProvider>();
    final server = provider.currentServer;
    if (server == null) return;

    setState(() => _isLoading = true);
    try {
      await GameServerFactoryService.stopServer(server.serverId);
      provider.updateServerStatus(server.serverId, 'stopped');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('服务器已停止'), backgroundColor: AppColors.success),
        );
      }
    } on NetworkException catch (e) {
      _showError(e.message);
    } on ApiException catch (e) {
      _showError(e.message);
    } catch (e) {
      _showError('停止服务器失败: ${e.toString()}');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _deleteServer() async {
    final provider = context.read<GameServerProvider>();
    final server = provider.currentServer;
    if (server == null) return;

    setState(() => _isLoading = true);
    try {
      await GameServerFactoryService.deleteServer(server.serverId);
      provider.removeServer(server.serverId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('服务器已删除'), backgroundColor: AppColors.success),
        );
        Navigator.pop(context);
      }
    } on NetworkException catch (e) {
      _showError(e.message);
    } on ApiException catch (e) {
      _showError(e.message);
    } catch (e) {
      _showError('删除服务器失败: ${e.toString()}');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message), backgroundColor: AppColors.error),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<GameServerProvider>(
      builder: (context, provider, child) {
        final server = provider.currentServer;
        
        if (server == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Server Details')),
            body: const Center(child: Text('No server selected')),
          );
        }

        return Scaffold(
          appBar: AppBar(
            title: Text(server.name),
            actions: [
              IconButton(
                icon: _isLoading 
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.refresh),
                onPressed: _isLoading ? null : _refreshServer,
              ),
            ],
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Status card
                _StatusCard(server: server),
                
                const SizedBox(height: 16),
                
                // Server info card
                _InfoCard(server: server),
                
                const SizedBox(height: 16),
                
                // Resource usage card
                _ResourceCard(server: server),
                
                const SizedBox(height: 16),
                
                // Logs card
                _LogsCard(server: server),
                
                const SizedBox(height: 24),
                
                // Action buttons
                _ActionButtons(
                  server: server,
                  onStop: _stopServer,
                  onDelete: _deleteServer,
                  isLoading: _isLoading,
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _StatusCard extends StatelessWidget {
  final GameServerInstance server;

  const _StatusCard({required this.server});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: AppColors.getStatusColor(server.status).withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: Icon(
                _getStatusIcon(server.status),
                size: 32,
                color: AppColors.getStatusColor(server.status),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    server.status.toUpperCase(),
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: AppColors.getStatusColor(server.status),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _getStatusDescription(server.status),
                    style: const TextStyle(color: AppColors.textSecondary),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  IconData _getStatusIcon(String status) {
    switch (status.toLowerCase()) {
      case 'running':
        return Icons.play_circle_filled;
      case 'creating':
        return Icons.hourglass_top;
      case 'stopped':
        return Icons.stop_circle;
      case 'error':
        return Icons.error;
      default:
        return Icons.help;
    }
  }

  String _getStatusDescription(String status) {
    switch (status.toLowerCase()) {
      case 'running':
        return 'Server is running and accepting connections';
      case 'creating':
        return 'Server is being created...';
      case 'stopped':
        return 'Server has been stopped';
      case 'error':
        return 'Server encountered an error';
      default:
        return 'Unknown status';
    }
  }
}

class _InfoCard extends StatelessWidget {
  final GameServerInstance server;

  const _InfoCard({required this.server});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Server Information',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const Divider(),
            _InfoRow(label: 'Server ID', value: server.serverId),
            _InfoRow(label: 'Port', value: server.port.toString()),
            _InfoRow(label: 'Container ID', value: server.containerId.isEmpty 
                ? 'N/A' 
                : server.containerId.substring(0, 12)),
            _InfoRow(label: 'Created', value: _formatDateTime(server.createdAt)),
            _InfoRow(label: 'Updated', value: _formatDateTime(server.updatedAt)),
            if (server.description.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                'Description',
                style: const TextStyle(
                  fontWeight: FontWeight.w500,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 4),
              Text(server.description),
            ],
          ],
        ),
      ),
    );
  }

  String _formatDateTime(DateTime dt) {
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} '
           '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(color: AppColors.textSecondary),
          ),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}

class _ResourceCard extends StatelessWidget {
  final GameServerInstance server;

  const _ResourceCard({required this.server});

  @override
  Widget build(BuildContext context) {
    final cpuValue = (server.resourceUsage['cpu_percent'] as num?)?.toDouble() ?? 0.0;
    final memoryValue = (server.resourceUsage['memory_mb'] as num?)?.toDouble() ?? 0.0;
    final network = server.resourceUsage['network_io'] ?? 'N/A';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Resource Usage',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const Divider(),
            _ResourceRow(
              icon: Icons.memory,
              label: 'CPU',
              value: '${cpuValue.toStringAsFixed(1)}%',
              progress: cpuValue / 100,
              color: _getResourceColor(cpuValue),
            ),
            const SizedBox(height: 12),
            _ResourceRow(
              icon: Icons.storage,
              label: 'Memory',
              value: '${memoryValue.toInt()} MB',
              progress: memoryValue / 512, // Assuming 512MB limit
              color: _getResourceColor(memoryValue / 512 * 100),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.network_check, size: 20, color: AppColors.textSecondary),
                const SizedBox(width: 8),
                const Text('Network I/O: '),
                Text(
                  network.toString(),
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Color _getResourceColor(double percentage) {
    if (percentage < 50) return AppColors.success;
    if (percentage < 80) return AppColors.warning;
    return AppColors.error;
  }
}

class _ResourceRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final double progress;
  final Color color;

  const _ResourceRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.progress,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 20, color: AppColors.textSecondary),
            const SizedBox(width: 8),
            Text(label),
            const Spacer(),
            Text(value, style: const TextStyle(fontWeight: FontWeight.w500)),
          ],
        ),
        const SizedBox(height: 4),
        LinearProgressIndicator(
          value: progress.clamp(0.0, 1.0),
          backgroundColor: color.withValues(alpha: 0.2),
          valueColor: AlwaysStoppedAnimation<Color>(color),
        ),
      ],
    );
  }
}

class _LogsCard extends StatelessWidget {
  final GameServerInstance server;

  const _LogsCard({required this.server});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Logs',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                TextButton.icon(
                  onPressed: () {
                    // TODO: Implement full logs view
                  },
                  icon: const Icon(Icons.open_in_new, size: 16),
                  label: const Text('View All'),
                ),
              ],
            ),
            const Divider(),
            Container(
              height: 150,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.black87,
                borderRadius: BorderRadius.circular(8),
              ),
              child: server.logs.isEmpty
                  ? const Center(
                      child: Text(
                        'No logs available',
                        style: TextStyle(color: Colors.white54),
                      ),
                    )
                  : ListView.builder(
                      itemCount: server.logs.length,
                      itemBuilder: (context, index) {
                        return Text(
                          server.logs[index],
                          style: const TextStyle(
                            fontFamily: 'monospace',
                            fontSize: 12,
                            color: Colors.greenAccent,
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActionButtons extends StatelessWidget {
  final GameServerInstance server;
  final VoidCallback onStop;
  final VoidCallback onDelete;
  final bool isLoading;

  const _ActionButtons({
    required this.server,
    required this.onStop,
    required this.onDelete,
    required this.isLoading,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        if (server.isRunning)
          Expanded(
            child: OutlinedButton.icon(
              onPressed: isLoading ? null : () {
                _showConfirmDialog(
                  context,
                  'Stop Server',
                  'Are you sure you want to stop this server?',
                  () {
                    Navigator.pop(context);
                    onStop();
                  },
                );
              },
              icon: const Icon(Icons.stop),
              label: const Text('Stop'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.warning,
              ),
            ),
          ),
        if (server.isStopped) ...[
          Expanded(
            child: ElevatedButton.icon(
              onPressed: isLoading ? null : () {
                // Restart is not yet implemented in the backend
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('重启功能暂未实现')),
                );
              },
              icon: const Icon(Icons.play_arrow),
              label: const Text('Start'),
            ),
          ),
          const SizedBox(width: 12),
        ],
        if (!server.isCreating)
          Expanded(
            child: OutlinedButton.icon(
              onPressed: isLoading ? null : () {
                _showConfirmDialog(
                  context,
                  'Delete Server',
                  'Are you sure you want to delete this server? This action cannot be undone.',
                  () {
                    Navigator.pop(context);
                    onDelete();
                  },
                );
              },
              icon: const Icon(Icons.delete),
              label: const Text('Delete'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.error,
              ),
            ),
          ),
      ],
    );
  }

  void _showConfirmDialog(
    BuildContext context,
    String title,
    String message,
    VoidCallback onConfirm,
  ) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: onConfirm,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
            ),
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
  }
}
