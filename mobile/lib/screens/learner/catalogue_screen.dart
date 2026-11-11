import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';
import '../../providers/providers.dart';
import 'practice_screen.dart';

class CatalogueScreen extends ConsumerWidget {
  const CatalogueScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final passagesAsync = ref.watch(cataloguePassagesProvider);
    final selectedFilter = ref.watch(catalogueFilterProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('مكتبة النصوص التدريبية'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.refresh(cataloguePassagesProvider),
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                FilterChip(
                  label: const Text('الكل'),
                  selected: selectedFilter == null,
                  onSelected: (_) => ref.read(catalogueFilterProvider.notifier).setFilter(null),
                ),
                const SizedBox(width: 8),
                ...['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map((lvl) {
                  return Padding(
                    padding: const EdgeInsets.only(left: 8),
                    child: FilterChip(
                      label: Text(lvl),
                      selected: selectedFilter == lvl,
                      onSelected: (_) => ref.read(catalogueFilterProvider.notifier).setFilter(lvl),
                    ),
                  );
                }),
              ],
            ),
          ),
          Expanded(
            child: passagesAsync.when(
              data: (passages) {
                if (passages.isEmpty) {
                  return const Center(child: Text('لا توجد نصوص متوفرة حالياً'));
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: passages.length,
                  itemBuilder: (context, idx) {
                    final p = passages[idx];
                    return Card(
                      key: Key('passageCard_${p.passageId}'),
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        title: Text(
                          p.topic,
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Text(
                          p.text,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        trailing: Chip(
                          label: Text(p.level),
                          backgroundColor: AppConstants.accentGold.withValues(alpha: 0.2),
                        ),
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => PracticeScreen(passage: p),
                            ),
                          );
                        },
                      ),
                    );
                  },
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, stack) => Center(
                child: Text('خطأ في تحميل المكتبة: $err'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
