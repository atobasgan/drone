import 'package:flutter/material.dart';

/// Kullanıcının sesini aldığında canlı ses dalgaları ve söylenen/anlaşılan komutu
/// ekranda net bir şekilde gösteren görsel widget.
class VoiceVisualizerWidget extends StatefulWidget {
  final bool isListening;
  final bool isProcessing;
  final bool isRecognized;
  final String? recognizedText;
  final String? recognizedAction;
  final String? errorMessage;

  const VoiceVisualizerWidget({
    super.key,
    required this.isListening,
    this.isProcessing = false,
    this.isRecognized = false,
    this.recognizedText,
    this.recognizedAction,
    this.errorMessage,
  });

  @override
  State<VoiceVisualizerWidget> createState() => _VoiceVisualizerWidgetState();
}

class _VoiceVisualizerWidgetState extends State<VoiceVisualizerWidget>
    with TickerProviderStateMixin {
  late List<AnimationController> _controllers;
  late List<Animation<double>> _animations;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    // 5 çubuklu ses dalgası animasyonu
    _controllers = List.generate(5, (index) {
      return AnimationController(
        vsync: this,
        duration: Duration(milliseconds: 280 + (index * 85)),
      );
    });

    _animations = _controllers.map((c) {
      return Tween<double>(begin: 6.0, end: 36.0).animate(
        CurvedAnimation(parent: c, curve: Curves.easeInOut),
      );
    }).toList();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _pulseAnimation = Tween<double>(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _updateAnimation();
  }

  @override
  void didUpdateWidget(covariant VoiceVisualizerWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isListening != oldWidget.isListening ||
        widget.isProcessing != oldWidget.isProcessing) {
      _updateAnimation();
    }
  }

  void _updateAnimation() {
    if (widget.isListening) {
      for (var c in _controllers) {
        if (!c.isAnimating) c.repeat(reverse: true);
      }
      if (!_pulseController.isAnimating) _pulseController.repeat(reverse: true);
    } else {
      for (var c in _controllers) {
        c.stop();
        c.animateTo(0.15);
      }
      _pulseController.stop();
    }
  }

  @override
  void dispose() {
    for (var c in _controllers) {
      c.dispose();
    }
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    Color statusColor = Colors.grey.shade600;
    String statusTitle = 'MİKROFON HAZIR';
    IconData statusIcon = Icons.mic_none;

    if (widget.isListening) {
      statusColor = const Color(0xFF00E676); // Canlı Yeşil
      statusTitle = 'SES DİNLENİYOR (CANLI)';
      statusIcon = Icons.hearing;
    } else if (widget.isProcessing) {
      statusColor = Colors.lightBlueAccent;
      statusTitle = 'KOMUT ÇÖZÜMLENİYOR...';
      statusIcon = Icons.auto_awesome;
    } else if (widget.isRecognized) {
      statusColor = const Color(0xFF00E676);
      statusTitle = 'KOMUT ANLAŞILDI ✓';
      statusIcon = Icons.check_circle;
    } else if (widget.errorMessage != null) {
      statusColor = const Color(0xFFFF5252);
      statusTitle = 'KOMUT ANLAŞILAMADI';
      statusIcon = Icons.error_outline;
    }

    final hasText = widget.recognizedText != null &&
        widget.recognizedText!.trim().isNotEmpty;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: statusColor.withValues(alpha: widget.isListening ? 0.9 : 0.4),
          width: widget.isListening ? 2.2 : 1.2,
        ),
        boxShadow: widget.isListening || widget.isRecognized
            ? [
                BoxShadow(
                  color: statusColor.withValues(alpha: 0.25),
                  blurRadius: 18,
                  spreadRadius: 2,
                )
              ]
            : [],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Üst durum çubuğu & Canlı Ses Dalgası
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Dar ekranlarda başlık taşmasın: kalan alana sığdır, sığmazsa kısalt.
              Expanded(
                child: Row(
                  children: [
                    Icon(statusIcon, color: statusColor, size: 20),
                    const SizedBox(width: 8),
                    Flexible(
                      child: Text(
                        statusTitle,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: statusColor,
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.0,
                        ),
                      ),
                    ),
                    if (widget.isListening) ...[
                      const SizedBox(width: 8),
                      AnimatedBuilder(
                        animation: _pulseAnimation,
                        builder: (context, _) => Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.red
                                .withValues(alpha: _pulseAnimation.value),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: const Text(
                            'CANLI',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 8),
              // Canlı Ses Dalgası Çubukları
              Row(
                children: List.generate(_animations.length, (i) {
                  return AnimatedBuilder(
                    animation: _animations[i],
                    builder: (context, _) {
                      return Container(
                        margin: const EdgeInsets.symmetric(horizontal: 2),
                        width: 4,
                        height: widget.isListening ? _animations[i].value : 8.0,
                        decoration: BoxDecoration(
                          color: statusColor,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      );
                    },
                  );
                }),
              ),
            ],
          ),

          const SizedBox(height: 12),

          // Söylenen Metin Alanı (Kullanıcının ne dediğini görmesini sağlar)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF21262D),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: hasText
                    ? (widget.isRecognized
                        ? const Color(0xFF00E676).withValues(alpha: 0.5)
                        : Colors.white24)
                    : Colors.transparent,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Wrap: dar ekranda iki etiket yan yana sığmazsa alt satıra geçer.
                Wrap(
                  alignment: WrapAlignment.spaceBetween,
                  spacing: 8,
                  runSpacing: 2,
                  children: [
                    Text(
                      widget.isListening
                          ? 'SÖYLEDİĞİNİZ (DİNLENİYOR):'
                          : 'SÖYLENEN METİN:',
                      style: TextStyle(
                        color: widget.isListening
                            ? const Color(0xFF00E676)
                            : Colors.grey.shade400,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                      ),
                    ),
                    if (widget.isListening && !hasText)
                      const Text(
                        'Konuşmanız bekleniyor...',
                        style: TextStyle(
                          color: Colors.grey,
                          fontSize: 11,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  hasText
                      ? '"${widget.recognizedText}"'
                      : (widget.isListening
                          ? 'Mikrofona konuşun...'
                          : 'Henüz bir ses algılanmadı.'),
                  style: TextStyle(
                    color: hasText ? Colors.white : Colors.grey.shade500,
                    fontSize: 17,
                    fontWeight: hasText ? FontWeight.bold : FontWeight.normal,
                    letterSpacing: 0.5,
                  ),
                ),
                if (widget.recognizedAction != null) ...[
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      const Text(
                        'UYGULANAN EYLEM: ',
                        style: TextStyle(
                          color: Colors.grey,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 3),
                        decoration: BoxDecoration(
                          color: const Color(0xFF00E676).withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(
                              color: const Color(0xFF00E676), width: 1),
                        ),
                        child: Text(
                          widget.recognizedAction!,
                          style: const TextStyle(
                            color: Color(0xFF00E676),
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),

          // Hata / Uyarı Mesajı (varsa)
          if (widget.errorMessage != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFFFF5252).withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                    color: const Color(0xFFFF5252).withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline,
                      color: Color(0xFFFF5252), size: 16),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      widget.errorMessage!,
                      style: const TextStyle(
                        color: Color(0xFFFF5252),
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],

          // Alt bilgi ipucu
          if (!widget.isListening &&
              widget.errorMessage == null &&
              !hasText) ...[
            const SizedBox(height: 8),
            const Text(
              'Aşağıdaki mikrofona basılı tutarak konuşun ("İleri", "Yüksel", "Dur")',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.grey,
                fontSize: 11,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
