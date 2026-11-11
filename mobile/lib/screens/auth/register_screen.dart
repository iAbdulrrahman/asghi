import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';
import '../../models/models.dart';
import '../../providers/providers.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _identController = TextEditingController();
  final _passController = TextEditingController();
  final _nameController = TextEditingController();
  String _selectedLevel = 'B1';
  UserRole _selectedRole = UserRole.learner;
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _identController.dispose();
    _passController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  void _register() async {
    if (!_formKey.currentState!.validate()) return;
    final notifier = ref.read(authProvider.notifier);
    final regSuccess = await notifier.register(
      _identController.text.trim(),
      _passController.text,
    );
    if (!regSuccess) {
      if (mounted) {
        final err = ref.read(authProvider).errorMessage ?? 'فشل التسجيل';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(err), backgroundColor: AppConstants.errorRed),
        );
      }
      return;
    }
    // Complete profile
    await notifier.completeProfile(
      _nameController.text.trim(),
      _selectedLevel,
      _selectedRole,
    );
    if (mounted) {
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('إنشاء حساب جديد')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _identController,
                decoration: const InputDecoration(
                  labelText: 'البريد الإلكتروني أو رقم الهاتف',
                  prefixIcon: Icon(Icons.contact_mail),
                ),
                validator: (v) => (v == null || v.isEmpty) ? 'مطلوب' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'الاسم المعروض',
                  prefixIcon: Icon(Icons.person),
                ),
                validator: (v) => (v == null || v.isEmpty) ? 'مطلوب' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _passController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'كلمة المرور',
                  prefixIcon: Icon(Icons.lock),
                ),
                validator: (v) => (v == null || v.length < 6) ? '6 أحرف على الأقل' : null,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                initialValue: _selectedLevel,
                decoration: const InputDecoration(labelText: 'مستوى اللغة العربية'),
                items: ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
                    .map((l) => DropdownMenuItem(value: l, child: Text(l)))
                    .toList(),
                onChanged: (v) => setState(() => _selectedLevel = v ?? 'B1'),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<UserRole>(
                initialValue: _selectedRole,
                decoration: const InputDecoration(labelText: 'الدور المطلوب'),
                items: UserRole.values
                    .map((r) => DropdownMenuItem(value: r, child: Text(r.displayNameArabic)))
                    .toList(),
                onChanged: (v) => setState(() => _selectedRole = v ?? UserRole.learner),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _register,
                child: const Text('تسجيل الحساب'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
