import 'package:flutter/material.dart';
import 'package:drone_voice_control/presentation/blocs/connection/connection_event.dart';

/// Bağlantı durumu göstergesi widget'ı
///
/// Küçük bir renkli nokta ve host:port metni gösterir.
/// Dokunulduğunda yeniden bağlanma tetiklenir.
class ConnectionIndicator extends StatelessWidget {
  /// Bağlantı durumu
  final ConnectionStatus status;

  /// Bağlı olunan host adresi
  final String host;

  /// Bağlı olunan port numarası
  final int port;

  /// Dokunulduğunda tetiklenen yeniden bağlanma callback'i
  final VoidCallback? onReconnectTap;

  const ConnectionIndicator({
    super.key,
    ConnectionStatus? status,
    bool? isConnected,
    this.host = '',
    this.port = 0,
    this.onReconnectTap,
  }) : status = status ??
            (isConnected == true
                ? ConnectionStatus.connected
                : ConnectionStatus.disconnected);

  /// Duruma göre gösterge rengi
  Color _getStatusColor() {
    switch (status) {
      case ConnectionStatus.connected:
        return const Color(0xFF00E676); // Yeşil
      case ConnectionStatus.connecting:
        return const Color(0xFFFFD740); // Sarı
      case ConnectionStatus.disconnected:
        return Colors.grey; // Gri
      case ConnectionStatus.error:
        return const Color(0xFFFF1744); // Kırmızı
    }
  }

  /// Duruma göre metin
  String _getStatusText() {
    switch (status) {
      case ConnectionStatus.connected:
        return host.isNotEmpty ? '$host:$port' : 'Bağlı';
      case ConnectionStatus.connecting:
        return 'Bağlanıyor...';
      case ConnectionStatus.disconnected:
        return 'Bağlantı Yok';
      case ConnectionStatus.error:
        return 'Bağlantı Hatası';
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getStatusColor();

    return GestureDetector(
      onTap: onReconnectTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: color.withValues(alpha: 0.3),
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Animasyonlu durum noktası
            _AnimatedDot(color: color, isAnimating: status == ConnectionStatus.connecting),
            const SizedBox(width: 6),
            // Durum metni
            Text(
              _getStatusText(),
              style: TextStyle(
                color: color,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
            // Yeniden bağlan ikonu (bağlı değilse)
            if (status != ConnectionStatus.connected &&
                status != ConnectionStatus.connecting) ...[
              const SizedBox(width: 4),
              Icon(
                Icons.refresh,
                color: color,
                size: 14,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Animasyonlu durum noktası
class _AnimatedDot extends StatefulWidget {
  final Color color;
  final bool isAnimating;

  const _AnimatedDot({
    required this.color,
    required this.isAnimating,
  });

  @override
  State<_AnimatedDot> createState() => _AnimatedDotState();
}

class _AnimatedDotState extends State<_AnimatedDot>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _animation = Tween<double>(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    if (widget.isAnimating) {
      _controller.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(covariant _AnimatedDot oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isAnimating && !_controller.isAnimating) {
      _controller.repeat(reverse: true);
    } else if (!widget.isAnimating && _controller.isAnimating) {
      _controller.stop();
      _controller.value = 1.0;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: widget.color.withValues(alpha: 
              widget.isAnimating ? _animation.value : 1.0,
            ),
            boxShadow: [
              BoxShadow(
                color: widget.color.withValues(alpha: 0.4),
                blurRadius: 4,
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}
