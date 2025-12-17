import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/game_server_provider.dart';
import '../models/game_server_instance.dart';
import '../services/game_server_factory_service.dart';
import '../theme/colors.dart';
import '../routes/app_routes.dart';

/// Screen displaying the user's created game servers.
/// Allows viewing server status, managing lifecycle, and navigating to details.
class MyServersScreen extends StatefulWidget {
  const MyServersScreen({super.key});

  @override
  State<MyServersScreen> createState() => _MyServersScreenState();
}

class _MyServersScreenState extends State<MyServersScreen> {
  @override
  void initState() {
    super.initState();
    // Load servers when screen initializes
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadServers();
    });
  }

  Future<void> _loadServers() async {
    final provider = context.read<GameServerProvider>();
    provider.setLoading(true);
    provider.clearError();

    try {
      final servers = await GameServerFactoryService.fetchMyServers();
      provider.setServers(servers);
    } on NetworkException catch (e) {
      provider.setError(e.message);
    } on ApiException catch (e) {
      provider.setError(e.message);
    } catch (e) {
      provider.setError('加载服务器列表失败: ${e.toString()}');
    } finally {
      provider.setLoading(false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Servers'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadServers,
          ),
        ],
      ),
      body: Consumer<GameServerProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.errorMessage != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 64, color: AppColors.error),
                  const SizedBox(height: 16),
                  Text(provider.errorMessage!),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.clearError(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (provider.myServers.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.dns_outlined, size: 64, color: AppColors.textSecondary),
                  const SizedBox(height: 16),
                  const Text('No servers yet'),
                  const SizedBox(height: 8),
                  const Text(
                    'Upload your JavaScript code to create a game server',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    onPressed: () {
                      Navigator.pushNamed(context, AppRoutes.uploadCode);
                    },
                    icon: const Icon(Icons.upload_file),
                    label: const Text('Upload Code'),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: provider.myServers.length,
            itemBuilder: (context, index) {
              final server = provider.myServers[index];
              return _ServerCard(server: server);
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.pushNamed(context, AppRoutes.uploadCode);
        },
        icon: const Icon(Icons.add),
        label: const Text('New Server'),
      ),
    );
  }
}

class _ServerCard extends StatelessWidget {
  final GameServerInstance server;

  const _ServerCard({required this.server});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () {
          context.read<GameServerProvider>().setCurrentServer(server);
          Navigator.pushNamed(context, AppRoutes.serverDetail);
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      server.name,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  _StatusChip(status: server.status),
                ],
              ),
              if (server.description.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  server.description,
                  style: const TextStyle(color: AppColors.textSecondary),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(Icons.link, size: 16, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Text(
                    'Port: ${server.port}',
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                  ),
                  const Spacer(),
                  Text(
                    _formatDate(server.createdAt),
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);
    
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inHours < 1) return '${diff.inMinutes}m ago';
    if (diff.inDays < 1) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    
    return '${date.month}/${date.day}/${date.year}';
  }
}

class _StatusChip extends StatelessWidget {
  final String status;

  const _StatusChip({required this.status});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.getStatusColor(status).withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.getStatusColor(status),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: AppColors.getStatusColor(status),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            status.toUpperCase(),
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: AppColors.getStatusColor(status),
            ),
          ),
        ],
      ),
    );
  }
}
