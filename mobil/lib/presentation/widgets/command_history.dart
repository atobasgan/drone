import 'package:flutter/material.dart';

/// Sesli komut geçmişi listesi
///
/// Son yapılan sesli komutları kaydırılabilir bir liste
/// olarak gösterir. Her giriş tanınan metin, komut tipi,
/// zaman damgası ve başarı/hata simgesi içerir.
class CommandHistory extends StatelessWidget {
  /// Komut geçmişi listesi
  final List<CommandHistoryEntry> entries;

  /// Maksimum gösterilecek giriş sayısı
  final int maxEntries;

  CommandHistory({
    super.key,
    List<CommandHistoryEntry>? entries,
    List<dynamic>? commands,
    this.maxEntries = 50,
  }) : entries = entries ??
            (commands?.map((c) {
                  if (c is CommandHistoryEntry) return c;
                  return CommandHistoryEntry(
                    recognizedText: c.toString(),
                    commandDescription: c.toString(),
                    timestamp: DateTime.now(),
                  );
                }).toList() ??
                const []);

  @override
  Widget build(BuildContext context) {
    final displayEntries = entries.length > maxEntries
        ? entries.sublist(entries.length - maxEntries)
        : entries;

    if (displayEntries.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF1E1E2C),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.history,
                color: Colors.grey.shade600,
                size: 40,
              ),
              const SizedBox(height: 8),
              Text(
                'Henüz komut yok',
                style: TextStyle(
                  color: Colors.grey.shade500,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Mikrofon butonuna basılı tutarak konuşun',
                style: TextStyle(
                  color: Colors.grey.shade600,
                  fontSize: 12,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E2C),
        borderRadius: BorderRadius.circular(12),
      ),
      child: ListView.separated(
        shrinkWrap: true,
        // Uçuş ekranının kaydırma alanı içinde; kendi başına kaymasın.
        physics: const NeverScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(vertical: 8),
        itemCount: displayEntries.length,
        separatorBuilder: (_, __) => Divider(
          color: Colors.grey.shade800,
          height: 1,
          indent: 48,
        ),
        itemBuilder: (context, index) {
          // Ters sıralama - en yeni üstte
          final entry = displayEntries[displayEntries.length - 1 - index];
          return _buildCommandTile(entry);
        },
      ),
    );
  }

  /// Tek komut satırı widget'ı
  Widget _buildCommandTile(CommandHistoryEntry entry) {
    final statusColor = entry.isSuccess
        ? const Color(0xFF00E676)
        : const Color(0xFFFF1744);
    final statusIcon = entry.isSuccess ? Icons.check_circle : Icons.error;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Başarı/hata simgesi
          Icon(statusIcon, color: statusColor, size: 20),
          const SizedBox(width: 12),
          // İçerik
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Tanınan metin
                Text(
                  '"${entry.recognizedText}"',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontStyle: FontStyle.italic,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                // Komut tipi
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: const Color(0xFF00E5FF).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    entry.commandDescription,
                    style: const TextStyle(
                      color: Color(0xFF00E5FF),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          // Zaman damgası
          Text(
            _formatTime(entry.timestamp),
            style: TextStyle(
              color: Colors.grey.shade600,
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }

  /// Zaman damgasını formatla
  String _formatTime(DateTime timestamp) {
    final hour = timestamp.hour.toString().padLeft(2, '0');
    final minute = timestamp.minute.toString().padLeft(2, '0');
    final second = timestamp.second.toString().padLeft(2, '0');
    return '$hour:$minute:$second';
  }
}

/// Komut geçmişi girişi veri modeli
class CommandHistoryEntry {
  /// Tanınan ses metni
  final String recognizedText;

  /// Komut açıklaması (ör: "İleri Git", "Kalkış")
  final String commandDescription;

  /// Zaman damgası
  final DateTime timestamp;

  /// Komut başarılı mı?
  final bool isSuccess;

  /// Güven skoru (0-1)
  final double confidence;

  const CommandHistoryEntry({
    required this.recognizedText,
    required this.commandDescription,
    required this.timestamp,
    this.isSuccess = true,
    this.confidence = 1.0,
  });
}
