import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Sesli komut için büyük animasyonlu mikrofon butonu
///
/// Basılı tutarak konuşma (push-to-talk) mekanizması ile çalışır.
/// Duruma göre renk ve animasyon değiştirir:
/// - Gri: Boşta
/// - Yeşil: Dinliyor
/// - Mavi: İşleniyor
/// - Kırmızı: Hata
class VoiceButton extends StatefulWidget {
  /// Uzun basma başladığında tetiklenir
  final VoidCallback? onListenStart;

  /// Uzun basma bittiğinde tetiklenir
  final VoidCallback? onListenStop;

  /// Butonun mevcut durumu
  final VoiceButtonState buttonState;

  /// Buton boyutu
  final double size;

  const VoiceButton({
    super.key,
    this.onListenStart,
    this.onListenStop,
    this.buttonState = VoiceButtonState.idle,
    this.size = 80,
  });

  @override
  State<VoiceButton> createState() => _VoiceButtonState();
}

class _VoiceButtonState extends State<VoiceButton>
    with TickerProviderStateMixin {
  late AnimationController _pulseController;
  late AnimationController _scaleController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();

    // Nabız animasyonu - dinleme sırasında genişleyen daireler
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.8).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeOut),
    );

    // Basma ölçek animasyonu
    _scaleController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 150),
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.92).animate(
      CurvedAnimation(parent: _scaleController, curve: Curves.easeInOut),
    );
  }

  @override
  void didUpdateWidget(covariant VoiceButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.buttonState != oldWidget.buttonState) {
      _updateAnimation();
    }
  }

  void _updateAnimation() {
    if (widget.buttonState == VoiceButtonState.listening) {
      _pulseController.repeat();
    } else {
      _pulseController.stop();
      _pulseController.reset();
    }
  }

  /// Duruma göre buton rengi
  Color _getButtonColor() {
    switch (widget.buttonState) {
      case VoiceButtonState.idle:
        return Colors.grey.shade700;
      case VoiceButtonState.listening:
        return const Color(0xFF00E676); // Yeşil
      case VoiceButtonState.processing:
        return const Color(0xFF00B0FF); // Mavi
      case VoiceButtonState.error:
        return const Color(0xFFFF1744); // Kırmızı
    }
  }

  /// Duruma göre parıltı rengi
  Color _getGlowColor() {
    switch (widget.buttonState) {
      case VoiceButtonState.idle:
        return Colors.grey.shade700.withValues(alpha: 0.3);
      case VoiceButtonState.listening:
        return const Color(0xFF00E676).withValues(alpha: 0.4);
      case VoiceButtonState.processing:
        return const Color(0xFF00B0FF).withValues(alpha: 0.4);
      case VoiceButtonState.error:
        return const Color(0xFFFF1744).withValues(alpha: 0.4);
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onLongPressStart: (_) {
        HapticFeedback.mediumImpact();
        _scaleController.forward();
        widget.onListenStart?.call();
      },
      onLongPressEnd: (_) {
        HapticFeedback.lightImpact();
        _scaleController.reverse();
        widget.onListenStop?.call();
      },
      child: AnimatedBuilder(
        animation: Listenable.merge([_pulseAnimation, _scaleAnimation]),
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: SizedBox(
              width: widget.size * 2.2,
              height: widget.size * 2.2,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Nabız daireleri (dinlerken)
                  if (widget.buttonState == VoiceButtonState.listening) ...[
                    // Dış nabız halkası
                    _buildPulseCircle(
                      _pulseAnimation.value * 1.2,
                      _getGlowColor().withValues(alpha: 
                        (1 - (_pulseAnimation.value - 1) / 0.8) * 0.3,
                      ),
                    ),
                    // Orta nabız halkası
                    _buildPulseCircle(
                      _pulseAnimation.value,
                      _getGlowColor().withValues(alpha: 
                        (1 - (_pulseAnimation.value - 1) / 0.8) * 0.5,
                      ),
                    ),
                  ],
                  // Ana buton
                  Container(
                    width: widget.size,
                    height: widget.size,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _getButtonColor(),
                      boxShadow: [
                        BoxShadow(
                          color: _getGlowColor(),
                          blurRadius: 20,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: Icon(
                      widget.buttonState == VoiceButtonState.error
                          ? Icons.mic_off
                          : Icons.mic,
                      color: Colors.white,
                      size: widget.size * 0.45,
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

  /// Nabız dairesi widget'ı
  Widget _buildPulseCircle(double scale, Color color) {
    return Transform.scale(
      scale: scale,
      child: Container(
        width: widget.size,
        height: widget.size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(color: color, width: 2),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _scaleController.dispose();
    super.dispose();
  }
}

/// Mikrofon butonunun olası durumları
enum VoiceButtonState {
  /// Boşta - basılmayı bekliyor
  idle,

  /// Aktif dinleme yapılıyor
  listening,

  /// Ses işleniyor / komut çözülüyor
  processing,

  /// Hata oluştu
  error,
}
