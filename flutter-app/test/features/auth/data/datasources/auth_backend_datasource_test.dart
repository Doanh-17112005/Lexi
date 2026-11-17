import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:lexilingo_app/core/network/api_client.dart';
import 'package:lexilingo_app/features/auth/data/datasources/auth_backend_datasource.dart';
import 'package:lexilingo_app/features/auth/data/datasources/device_manager.dart';
import 'package:lexilingo_app/features/auth/data/datasources/token_storage.dart';

class _RecordingApiClient extends ApiClient {
  Object? lastBody;
  Object? error;

  @override
  Future<Map<String, dynamic>> post(
    String path, {
    Map<String, String>? headers,
    Object? body,
    Duration? timeout,
  }) async {
    lastBody = body;
    if (error case final error?) throw error;
    return <String, dynamic>{};
  }
}

class _FakeTokenStorage extends TokenStorage {
  bool cleared = false;

  @override
  Future<String?> getRefreshToken() async => 'stored-refresh-token';

  @override
  Future<void> clearTokens() async {
    cleared = true;
  }
}

void main() {
  late _RecordingApiClient apiClient;
  late _FakeTokenStorage tokenStorage;
  late AuthBackendDataSource dataSource;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    apiClient = _RecordingApiClient();
    tokenStorage = _FakeTokenStorage();
    dataSource = AuthBackendDataSource(
      apiClient: apiClient,
      tokenStorage: tokenStorage,
      deviceManager: DeviceManager(),
    );
  });

  test('logout sends refresh token before clearing local tokens', () async {
    await dataSource.logout();

    expect(apiClient.lastBody, {'refresh_token': 'stored-refresh-token'});
    expect(tokenStorage.cleared, isTrue);
  });

  test('logout still clears local tokens when backend request fails', () async {
    apiClient.error = Exception('network unavailable');

    await dataSource.logout();

    expect(tokenStorage.cleared, isTrue);
  });
}
