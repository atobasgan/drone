import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:drone_voice_control/core/constants/app_constants.dart';
import 'package:drone_voice_control/core/theme/app_colors.dart';
import 'package:drone_voice_control/domain/entities/backend_feedback.dart';
import 'package:drone_voice_control/domain/repositories/voice_uplink_repository.dart';
import 'package:drone_voice_control/presentation/blocs/drone/drone_bloc.dart';
import 'package:drone_voice_control/presentation/blocs/drone/drone_state.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_bloc.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_event.dart';
import 'package:drone_voice_control/presentation/blocs/voice/voice_state.dart';
import 'package:drone_voice_control/presentation/screens/connection_log_screen.dart';
import 'package:drone_voice_control/presentation/widgets/telemetry_display.dart';
import 'package:drone_voice_control/presentation/widgets/compass_widget.dart';
import 'package:drone_voice_control/presentation/widgets/voice_button.dart';
import 'package:drone_voice_control/presentation/widgets/command_history.dart';
import 'package:drone_voice_control/presentation/widgets/voice_visualizer_widget.dart';
import 'package:drone_voice_control/presentation/widgets/command_popup.dart';
import 'package:drone_voice_control/data/datasources/tts_service.dart';
import 'package:drone_voice_control/di/injection_container.dart';

class FlightScreen extends StatefulWidget {
  const FlightScreen({super.key});

  @override
  State<FlightScreen> createState() => _FlightScreenState();
}

class _FlightScreenState extends State<FlightScreen> {
  final List<String> _history = [];
  String? _persistentSpokenText;
  String? _persistentAction;

  /// Backend geri bildirimlerini sesli okuyan servis
  final TtsService _tts = sl<TtsService>();

  /// Ses kaydını /voice/audio'ya, metni /voice/text'e gönderen; backend
  /// metnini (/voice/text) ve geri bildirimi (/drone/feedback) dinleyen depo
  final VoiceUplinkRepository _uplink = sl<VoiceUplinkRepository>();
  StreamSubscription<BackendFeedback>? _feedbackSub;
  StreamSubscription<String>? _transcriptSub;

  /// Ses gönderildi, backend'in yazıya çevirdiği metin bekleniyor.
  /// Bu bayrak, uygulamanın kendi gönderdiği metinlerin /voice/text'ten geri
  /// gelince "duyulan" diye gösterilmesini engeller.
  bool _awaitingTranscript = false;

  /// Son gönderilen ham metin (geri bildirimi pop-up'ta yanında göstermek için)
  String _lastSentText = '';

  /// Ekranda gösterilen komut pop-up'ı (yoksa null)
  KomutDuyurusu? _popup;
  Timer? _popupTimer;

  /// Pop-up'ın ekranda kalma süresi
  static const _popupSuresi = Duration(milliseconds: 1800);

  /// Sesli okunacak geri bildirim durumları (diğerleri yalnızca günlüğe yazılır)
  static const _spokenStates = {'yurutuyor', 'reddedildi', 'hata'};

  @override
  void initState() {
    super.initState();
    _feedbackSub = _uplink.feedbackStream.listen(_onBackendFeedback);
    _transcriptSub = _uplink.transcriptStream.listen(_onTranscript);
  }

  @override
  void dispose() {
    _feedbackSub?.cancel();
    _transcriptSub?.cancel();
    _popupTimer?.cancel();
    _tts.stop();
    super.dispose();
  }

  /// Ses kaydı backend'e yazıldı; metin backend STT'den gelecek.
  void _onVoiceAudioSent(VoiceAudioSent state) {
    _awaitingTranscript = true;
    final sn = (state.durationMs / 1000).toStringAsFixed(1);
    setState(() {
      _persistentSpokenText = null;
      _persistentAction = null;
      _history.add('🎤 ses gönderildi ($sn sn)');
    });
    _showCommandPopup(KomutDuyurusu.sesIletildi(state.durationMs));
  }

  /// Backend STT'nin ürettiği metin (/voice/text).
  void _onTranscript(String text) {
    if (!mounted || !_awaitingTranscript) return;
    _awaitingTranscript = false;
    _lastSentText = text;
    setState(() {
      _persistentSpokenText = text;
      _history.add('duyulan: "$text"');
    });
  }

  /// Hazır metin backend'e yazıldı. Komutun anlamı burada bilinmez.
  void _onVoiceTextSent(VoiceTextSent state) {
    _awaitingTranscript = false;
    _lastSentText = state.rawText;
    setState(() {
      _persistentSpokenText = state.rawText;
      _persistentAction = null;
      _history.add('→ ${state.rawText}');
    });
    _showCommandPopup(KomutDuyurusu.iletildi(state.rawText));
  }

  /// Backend'in /drone/feedback mesajı: günlüğe yazılır, pop-up'ta gösterilir.
  void _onBackendFeedback(BackendFeedback fb) {
    if (!mounted) return;
    setState(() {
      _persistentAction = fb.mesaj.toUpperCase();
      _history.add('[${fb.durum}] ${fb.mesaj}');
    });
    _showCommandPopup(KomutDuyurusu.geriBildirimden(fb, _lastSentText));
    if (_spokenStates.contains(fb.durum)) _tts.speak(fb.mesaj);
  }

  /// Duyuruyu pop-up olarak gösterir.
  void _showCommandPopup(KomutDuyurusu duyuru) {
    _popupTimer?.cancel();
    setState(() => _popup = duyuru);
    _popupTimer = Timer(_popupSuresi, () {
      if (mounted) setState(() => _popup = null);
    });
  }

  /// DURDUR: acil metnini mikrofon oturumundan bağımsız, hemen gönderir.
  void _sendEmergencyStop() {
    final sent = _uplink.sendRawText(AppConstants.emergencyStopText);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(sent
            ? '🛑 "${AppConstants.emergencyStopText}" gönderildi'
            : 'DURDUR gönderilemedi: rosbridge bağlantısı yok'),
        backgroundColor: AppColors.error,
      ),
    );
    if (sent) {
      _lastSentText = AppConstants.emergencyStopText;
      setState(() => _history.add('→ ${AppConstants.emergencyStopText}'));
    }
  }

  void _hidePopup() {
    _popupTimer?.cancel();
    if (_popup != null) setState(() => _popup = null);
  }

  void _simulateCommand(String text) {
    context.read<VoiceBloc>().add(VoiceResultReceived(text: text));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sesli Uçuş Kontrolü'),
        actions: [
          IconButton(
            tooltip: 'İletişim günlüğü',
            icon: const Icon(Icons.receipt_long),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ConnectionLogScreen()),
            ),
          ),
          // Acil Durum / Hover Butonu
          Padding(
            padding: const EdgeInsets.only(right: 8.0),
            child: ElevatedButton.icon(
              onPressed: _sendEmergencyStop,
              icon: const Icon(Icons.emergency, color: Colors.white),
              label: const Text('DURDUR',
                  style: TextStyle(
                      color: Colors.white, fontWeight: FontWeight.bold)),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.error,
                padding: const EdgeInsets.symmetric(horizontal: 12),
              ),
            ),
          ),
        ],
      ),
      body: MultiBlocListener(
        listeners: [
          BlocListener<VoiceBloc, VoiceState>(
            listener: (context, state) {
              if (state is VoiceAudioSent) {
                _onVoiceAudioSent(state);
              } else if (state is VoiceTextSent) {
                _onVoiceTextSent(state);
              } else if (state is VoiceError) {
                if (state.lastSpokenText == null) _tts.speak('Ses gönderilemedi');
                if (state.lastSpokenText != null &&
                    state.lastSpokenText!.isNotEmpty) {
                  setState(() {
                    _persistentSpokenText = state.lastSpokenText;
                    _persistentAction = null;
                  });
                  // Metin duyuldu ama backend'e gönderilemedi
                  _tts.speak('Komut gönderilemedi');
                }
              }
            },
          ),
        ],
        child: Stack(
          children: [
            Column(
              children: [
                // Telemetri, ses göstergesi, hızlı komutlar ve günlük birlikte
                // kayar: küçük ekranlarda telemetri ses alanını ezmesin.
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Orta Kısım: Canlı Ses Göstergesi ve Komut Geçmişi
                        Padding(
                          padding:
                              const EdgeInsets.all(AppConstants.defaultPadding),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              // Canlı ses görselleştirici & Söylenen metin
                              BlocBuilder<VoiceBloc, VoiceState>(
                                builder: (context, state) {
                                  bool isListening = state is VoiceListening;
                                  bool isProcessing = state is VoiceProcessing;
                                  bool isRecognized = state is VoiceTextSent ||
                                      state is VoiceAudioSent;
                                  String? recognizedText;
                                  String? recognizedAction = _persistentAction;
                                  String? errorMessage;

                                  if (state is VoiceListening) {
                                    // Yalnızca bu oturumda duyulanı göster; eski komut
                                    // "şu an söylenen" gibi görünmesin.
                                    recognizedText = state.partialText;
                                    recognizedAction = null;
                                  } else if (state is VoiceProcessing) {
                                    recognizedAction = null;
                                    recognizedText = state.rawText;
                                  } else if (state is VoiceTextSent) {
                                    recognizedText = state.rawText;
                                  } else if (state is VoiceAudioSent) {
                                    // Backend metni gelince _persistentSpokenText dolar
                                    recognizedText = _persistentSpokenText;
                                  } else if (state is VoiceError) {
                                    errorMessage = state.message;
                                    recognizedText = state.lastSpokenText ??
                                        _persistentSpokenText;
                                  } else {
                                    recognizedText = _persistentSpokenText;
                                  }

                                  return VoiceVisualizerWidget(
                                    isListening: isListening,
                                    isProcessing: isProcessing,
                                    isRecognized: isRecognized,
                                    recognizedText: recognizedText,
                                    recognizedAction: recognizedAction,
                                    errorMessage: errorMessage,
                                  );
                                },
                              ),

                              const SizedBox(height: 10),

                              // Hızlı komut düğmeleri: sabit ham metni konuşulmuş gibi gönderir
                              SingleChildScrollView(
                                scrollDirection: Axis.horizontal,
                                child: Row(
                                  children: [
                                    for (final (label, text)
                                        in AppConstants.quickCommands)
                                      _QuickCommandChip(
                                        label: label,
                                        onSelected: () => _simulateCommand(text),
                                      ),
                                  ],
                                ),
                              ),

                              const SizedBox(height: 10),

                              // Telemetri & Pusula (ses alanının altında: küçük ekranda onu itmesin)
                              ClipRRect(
                                borderRadius: BorderRadius.circular(12),
                                child: BlocBuilder<DroneBloc, DroneState>(
                                  builder: (context, state) {
                                    if (state is DroneConnected) {
                                      return Container(
                                        padding: const EdgeInsets.all(12),
                                        color: AppColors.surface,
                                        child: Row(
                                          children: [
                                            Expanded(
                                              flex: 2,
                                              child: TelemetryDisplay(
                                                  telemetry: state.telemetry),
                                            ),
                                            Expanded(
                                              flex: 1,
                                              child: CompassWidget(
                                                  yaw: state.telemetry.yaw),
                                            ),
                                          ],
                                        ),
                                      );
                                    }
                                    return Container(
                                      padding: const EdgeInsets.all(16),
                                      color: AppColors.surface,
                                      child: const Center(
                                        child: Text(
                                          'Drone Bağlantısı Bekleniyor...',
                                          style: TextStyle(
                                              color: AppColors.textSecondary),
                                        ),
                                      ),
                                    );
                                  },
                                ),
                              ),

                              const SizedBox(height: 10),

                              // Komut Geçmişi
                              const Text(
                                'Komut Günlüğü',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.textPrimary,
                                  fontSize: 13,
                                ),
                              ),
                              const SizedBox(height: 4),
                              CommandHistory(commands: _history),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // Alt Kısım: Sesli Komut Butonu (Push to Talk)
                Container(
                  padding: const EdgeInsets.only(bottom: 24, top: 6),
                  child: BlocBuilder<VoiceBloc, VoiceState>(
                    builder: (context, state) {
                      VoiceButtonState btnState = VoiceButtonState.idle;
                      if (state is VoiceListening) {
                        btnState = VoiceButtonState.listening;
                      } else if (state is VoiceProcessing) {
                        btnState = VoiceButtonState.processing;
                      } else if (state is VoiceError) {
                        btnState = VoiceButtonState.error;
                      }

                      return VoiceButton(
                        buttonState: btnState,
                        onListenStart: () {
                          // Konuşmaya başlarken önceki onay sussun ve mikrofona girmesin.
                          _tts.stop();
                          _hidePopup();
                          context.read<VoiceBloc>().add(const StartListening());
                        },
                        onListenStop: () {
                          context.read<VoiceBloc>().add(const StopListening());
                        },
                      );
                    },
                  ),
                ),
              ],
            ),

            // Eşleşen komut pop-up'ı (dokununca kapanır)
            Positioned.fill(
              child: IgnorePointer(
                ignoring: _popup == null,
                child: GestureDetector(
                  onTap: _hidePopup,
                  behavior: HitTestBehavior.opaque,
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 220),
                    transitionBuilder: (child, anim) => FadeTransition(
                      opacity: anim,
                      child: ScaleTransition(
                        scale: Tween<double>(begin: 0.85, end: 1.0).animate(
                          CurvedAnimation(
                              parent: anim, curve: Curves.easeOutBack),
                        ),
                        child: child,
                      ),
                    ),
                    child: _popup == null
                        ? const SizedBox.shrink()
                        : Container(
                            // Her komutta yeniden animasyon oynasın
                            key: ValueKey(_popupTimer.hashCode),
                            color: Colors.black.withValues(alpha: 0.35),
                            alignment: Alignment.center,
                            child: CommandPopup(duyuru: _popup!),
                          ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickCommandChip extends StatelessWidget {
  final String label;
  final VoidCallback onSelected;

  const _QuickCommandChip({
    required this.label,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 6.0),
      child: ActionChip(
        label: Text(
          label,
          style: const TextStyle(
              fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white),
        ),
        backgroundColor: const Color(0xFF21262D),
        side: const BorderSide(color: Color(0xFF30363D)),
        onPressed: onSelected,
      ),
    );
  }
}
