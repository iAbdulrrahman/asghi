import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'constants.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

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

  Future<String?> _safeReadToken() async {
    if (!useSecureStorage) return inMemoryToken;
    try {
      return await storage.read(key: 'jwt_token');
    } catch (_) {
      return inMemoryToken;
    }
  }

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

  Future<void> saveToken(String token) async {
    inMemoryToken = token;
    if (useSecureStorage) {
      try {
        await storage.write(key: 'jwt_token', value: token);
      } catch (_) {}
    }
  }

  Future<String?> getToken() async {
    if (inMemoryToken != null) return inMemoryToken;
    return await _safeReadToken();
  }

  Future<void> clearToken() async {
    inMemoryToken = null;
    if (useSecureStorage) {
      try {
        await storage.delete(key: 'jwt_token');
      } catch (_) {}
    }
  }
}
