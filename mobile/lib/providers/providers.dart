import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../core/audio_playback_service.dart';
import '../core/audio_recorder_service.dart';
import '../models/models.dart';

// --- Auth State ---
class AuthState {
  final User? user;
  final UserRole activeRole;
  final bool isLoading;
  final String? errorMessage;
  final bool isAuthenticated;

  AuthState({
    this.user,
    this.activeRole = UserRole.learner,
    this.isLoading = false,
    this.errorMessage,
    this.isAuthenticated = false,
  });

  AuthState copyWith({
    User? user,
    UserRole? activeRole,
    bool? isLoading,
    String? errorMessage,
    bool? isAuthenticated,
  }) {
    return AuthState(
      user: user ?? this.user,
      activeRole: activeRole ?? this.activeRole,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
    );
  }
}

class AuthNotifier extends Notifier<AuthState> {
  late final ApiClient apiClient;

  @override
  AuthState build() {
    apiClient = ref.watch(apiClientProvider);
    apiClient.onUnauthorized = () {
      logout();
    };
    apiClient.onNetworkError = (offline) {
      ref.read(isOfflineProvider.notifier).setOffline(offline);
    };
    _checkInitialAuth();
    return AuthState();
  }

  Future<void> _checkInitialAuth() async {
    final token = await apiClient.getToken();
    if (token != null && token.isNotEmpty) {
      await fetchCurrentUser();
    }
  }

  Future<bool> login(String identifier, String password) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final resp = await apiClient.dio.post('/api/auth/login', data: {
        'identifier': identifier,
        'password': password,
      });
      final token = resp.data['token'] ?? resp.data['accessToken'];
      await apiClient.saveToken(token);
      await fetchCurrentUser();
      return true;
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'فشل تسجيل الدخول';
      state = state.copyWith(isLoading: false, errorMessage: msg.toString());
      return false;
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
      return false;
    }
  }

  Future<bool> register(String emailOrPhone, String password) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final resp = await apiClient.dio.post('/api/auth/register', data: {
        'emailOrPhone': emailOrPhone,
        'password': password,
      });
      final token = resp.data['token'] ?? resp.data['accessToken'];
      if (token != null) {
        await apiClient.saveToken(token);
      }
      state = state.copyWith(isLoading: false);
      return true;
    } on DioException catch (e) {
      final msg = e.response?.data?['detail'] ?? 'فشل إنشاء الحساب';
      state = state.copyWith(isLoading: false, errorMessage: msg.toString());
      return false;
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
      return false;
    }
  }

  Future<bool> completeProfile(String displayName, String level, UserRole role) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final resp = await apiClient.dio.post('/api/users/profile', data: {
        'displayName': displayName,
        'level': level,
        'roleInterest': role.name.toUpperCase(),
      });
      final token = resp.data['token'];
      if (token != null) {
        await apiClient.saveToken(token);
      }
      await fetchCurrentUser();
      return true;
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
      return false;
    }
  }

  Future<void> fetchCurrentUser() async {
    try {
      final resp = await apiClient.dio.get('/api/users/me');
      final user = User.fromJson(resp.data);
      final active = user.roles.contains(state.activeRole)
          ? state.activeRole
          : (user.roles.isNotEmpty ? user.roles.first : UserRole.learner);
      state = state.copyWith(
        user: user,
        activeRole: active,
        isAuthenticated: true,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, isAuthenticated: false);
    }
  }

  void switchRole(UserRole newRole) {
    if (state.user?.roles.contains(newRole) == true) {
      state = state.copyWith(activeRole: newRole);
    }
  }

  Future<void> logout() async {
    await apiClient.clearToken();
    state = AuthState();
  }

  void setAuthenticatedUserForTesting(User user, UserRole role) {
    state = AuthState(
      user: user,
      activeRole: role,
      isAuthenticated: true,
      isLoading: false,
    );
  }
}

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final authProvider = NotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class OfflineNotifier extends Notifier<bool> {
  @override
  bool build() => false;

  void setOffline(bool offline) => state = offline;
}

final isOfflineProvider = NotifierProvider<OfflineNotifier, bool>(OfflineNotifier.new);

// --- Catalogue Provider ---
class CatalogueFilterNotifier extends Notifier<String?> {
  @override
  String? build() => null;

  void setFilter(String? newFilter) {
    state = newFilter;
  }
}

final catalogueFilterProvider = NotifierProvider<CatalogueFilterNotifier, String?>(CatalogueFilterNotifier.new);

final cataloguePassagesProvider = FutureProvider<List<Passage>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final filter = ref.watch(catalogueFilterProvider);
  final query = filter != null && filter.isNotEmpty ? '?level=$filter' : '';
  final resp = await client.dio.get('/api/passages$query');
  final list = (resp.data as List<dynamic>?) ?? [];
  return list.map((item) => Passage.fromJson(item as Map<String, dynamic>)).toList();
});


final audioRecorderProvider = Provider<AudioRecorderService>((ref) {
  final service = DeviceAudioRecorder();
  ref.onDispose(service.dispose);
  return service;
});
final audioPlaybackProvider = Provider<AudioPlaybackService>((ref) {
  final service = JustAudioPlaybackService();
  ref.onDispose(service.dispose);
  return service;
});
