import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'constants.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  static const String serverAddressStorageKey = 'custom_api_base_url';

  static dynamic parseData(dynamic data) {
    if (data is String) {
      try {
        return jsonDecode(data);
      } catch (_) {
        return data;
      }
    }
    return data;
  }

  late final Dio dio;
  final FlutterSecureStorage storage = const FlutterSecureStorage();
  String? inMemoryToken;
  bool useSecureStorage = true;
  void Function()? onUnauthorized;
  void Function(bool isOffline)? onNetworkError;

  ApiClient._internal() {
    dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Always ensure options.baseUrl uses current live apiBaseUrl if relative
          options.baseUrl = AppConstants.apiBaseUrl;
          final token = inMemoryToken ?? await _safeReadToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onResponse: (response, handler) {
          onNetworkError?.call(false);
          return handler.next(response);
        },
        onError: (DioException error, handler) async {
          if (error.response?.statusCode == 401) {
            inMemoryToken = null;
            if (useSecureStorage) {
              try {
                await storage.delete(key: 'jwt_token');
              } catch (_) {}
            }
            onUnauthorized?.call();
          }
          if (error.type == DioExceptionType.connectionTimeout ||
              error.type == DioExceptionType.connectionError ||
              error.type == DioExceptionType.receiveTimeout) {
            onNetworkError?.call(true);
          }
          return handler.next(error);
        },
      ),
    );
  }

  Future<void> initBaseUrl() async {
    if (useSecureStorage) {
      try {
        final saved = await storage.read(key: serverAddressStorageKey);
        if (saved != null && saved.isNotEmpty) {
          final normalized = AppConstants.normalizeAndValidateServerUrl(saved);
          if (normalized != null) {
            AppConstants.customBaseUrl = normalized;
            dio.options.baseUrl = normalized;
          }
        }
      } catch (_) {}
    }
  }

  Future<bool> setBaseUrl(String? newUrl) async {
    if (newUrl == null || newUrl.trim().isEmpty) {
      AppConstants.customBaseUrl = null;
      dio.options.baseUrl = AppConstants.defaultApiBaseUrl;
      if (useSecureStorage) {
        try {
          await storage.delete(key: serverAddressStorageKey);
        } catch (_) {}
      }
      return true;
    }

    final normalized = AppConstants.normalizeAndValidateServerUrl(newUrl);
    if (normalized == null) {
      return false;
    }

    AppConstants.customBaseUrl = normalized;
    dio.options.baseUrl = normalized;

    if (useSecureStorage) {
      try {
        await storage.write(key: serverAddressStorageKey, value: normalized);
      } catch (_) {}
    }
    return true;
  }

  Future<String?> _safeReadToken() async {
    if (!useSecureStorage) return null;
    try {
      return await storage.read(key: 'jwt_token');
    } catch (_) {
      return null;
    }
  }

  Future<void> saveToken(String token) async {
    inMemoryToken = token;
    if (useSecureStorage) {
      try {
        await storage.write(key: 'jwt_token', value: token);
      } catch (_) {}
    }
  }

  Future<void> clearToken() async {
    inMemoryToken = null;
    if (useSecureStorage) {
      try {
        await storage.delete(key: 'jwt_token');
      } catch (_) {}
    }
  }

  Future<String?> getToken() async {
    return inMemoryToken ?? await _safeReadToken();
  }
}
