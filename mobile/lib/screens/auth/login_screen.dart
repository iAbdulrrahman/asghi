import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';
import '../../core/api_client.dart';
import '../../providers/providers.dart';
import 'register_screen.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _identifierController = TextEditingController();
  final _passwordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _identifierController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final success = await ref.read(authProvider.notifier).login(
          _identifierController.text.trim(),
          _passwordController.text,
        );
    if (!success && mounted) {
      final err = ref.read(authProvider).errorMessage ?? 'خطأ في بيانات الدخول';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(err), backgroundColor: AppConstants.errorRed),
      );
    }
  }

  void _showServerSettingsDialog() {
    final controller = TextEditingController(text: AppConstants.apiBaseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('إعدادات عنوان الخادم', textDirection: TextDirection.rtl),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'أدخل عنوان خادم API (يدعم http و https):',
              style: TextStyle(fontSize: 13, color: Colors.grey),
              textDirection: TextDirection.rtl,
            ),
            const SizedBox(height: 12),
            TextField(
              key: const Key('server_address_field'),
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'مثال: https://invoicing.0xabdul.dev',
                prefixIcon: Icon(Icons.link),
              ),
              textDirection: TextDirection.ltr,
            ),
          ],
        ),
        actions: [
          TextButton(
            key: const Key('server_address_reset_button'),
            onPressed: () async {
              await ApiClient().setBaseUrl(null);
              if (mounted) {
                Navigator.of(context).pop();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('تمت استعادة عنوان الخادم الافتراضي')),
                );
              }
            },
            child: const Text('إعادة تعيين'),
          ),
          ElevatedButton(
            key: const Key('server_address_save_button'),
            onPressed: () async {
              final val = controller.text.trim();
              final success = await ApiClient().setBaseUrl(val);
              if (!success && mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('عنوان الخادم غير صالح. تأكد من إدخال عنوان صحيح.'),
                    backgroundColor: AppConstants.errorRed,
                  ),
                );
                return;
              }
              if (mounted) {
                Navigator.of(context).pop();
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('تم ضبط عنوان الخادم إلى: ${AppConstants.apiBaseUrl}'),
                    backgroundColor: AppConstants.successGreen,
                  ),
                );
              }
            },
            child: const Text('حفظ'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('تسجيل الدخول'),
        actions: [
          IconButton(
            key: const Key('server_settings_button'),
            icon: const Icon(Icons.dns_outlined),
            tooltip: 'إعدادات عنوان الخادم',
            onPressed: _showServerSettingsDialog,
          ),
        ],
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.record_voice_over, size: 64, color: AppConstants.primaryEmerald),
                const SizedBox(height: 12),
                const Text(
                  AppConstants.appNameArabic,
                  style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: AppConstants.primaryEmerald),
                ),
                const Text(AppConstants.appSubtitle, style: TextStyle(color: Colors.grey)),
                const SizedBox(height: 32),
                TextFormField(
                  key: const Key('identifierField'),
                  controller: _identifierController,
                  decoration: const InputDecoration(
                    labelText: 'البريد الإلكتروني أو رقم الهاتف',
                    prefixIcon: Icon(Icons.person),
                  ),
                  textDirection: TextDirection.ltr,
                  validator: (v) => (v == null || v.isEmpty) ? 'يرجى إدخال البريد أو الهاتف' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  key: const Key('passwordField'),
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'كلمة المرور',
                    prefixIcon: Icon(Icons.lock),
                  ),
                  validator: (v) => (v == null || v.isEmpty) ? 'يرجى إدخال كلمة المرور' : null,
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  key: const Key('loginButton'),
                  onPressed: authState.isLoading ? null : _submit,
                  child: authState.isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('دخول'),
                ),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const RegisterScreen()),
                    );
                  },
                  child: const Text('ليس لديك حساب؟ أنشئ حساباً جديداً'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
