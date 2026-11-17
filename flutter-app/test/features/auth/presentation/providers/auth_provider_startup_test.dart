import 'dart:async';

import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/core/services/facebook_sign_in_service.dart';
import 'package:lexilingo_app/core/services/google_sign_in_service.dart';
import 'package:lexilingo_app/features/auth/domain/entities/user_entity.dart';
import 'package:lexilingo_app/features/auth/domain/usecases/get_current_user_usecase.dart';
import 'package:lexilingo_app/features/auth/domain/usecases/register_usecase.dart';
import 'package:lexilingo_app/features/auth/domain/usecases/sign_in_with_email_password_usecase.dart';
import 'package:lexilingo_app/features/auth/domain/usecases/sign_in_with_facebook_usecase.dart';
import 'package:lexilingo_app/features/auth/domain/usecases/sign_in_with_google_usecase.dart';
import 'package:lexilingo_app/features/auth/domain/usecases/sign_out_usecase.dart';
import 'package:lexilingo_app/features/auth/presentation/providers/auth_provider.dart';

import '../../domain/usecases/login_usecase_test.mocks.dart';

class _FakeGoogleSignInService extends GoogleSignInService {
  _FakeGoogleSignInService({this.redirectResult, this.error});

  final Future<String?>? redirectResult;
  final String? error;

  @override
  String? get lastError => error;

  @override
  Future<String?> consumePendingWebRedirectIdToken() =>
      redirectResult ?? Future<String?>.value();

  @override
  Future<String?> signIn() async => null;
}

class _FakeFacebookSignInService extends FacebookSignInService {
  _FakeFacebookSignInService({this.error});

  final Object? error;

  @override
  Future<String?> signIn() async {
    if (error case final error?) throw error;
    return null;
  }
}

AuthProvider _provider({
  required MockAuthRepository repository,
  required GoogleSignInService google,
  FacebookSignInService? facebook,
}) {
  return AuthProvider(
    signInWithGoogleUseCase: SignInWithGoogleUseCase(repository),
    signInWithFacebookUseCase: SignInWithFacebookUseCase(repository),
    signInWithEmailPasswordUseCase: SignInWithEmailPasswordUseCase(repository),
    signOutUseCase: SignOutUseCase(repository),
    getCurrentUserUseCase: GetCurrentUserUseCase(repository),
    registerUseCase: RegisterUseCase(repository),
    authRepository: repository,
    googleSignInService: google,
    facebookSignInService: facebook ?? _FakeFacebookSignInService(),
    redirectRecoveryTimeout: const Duration(milliseconds: 10),
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late MockAuthRepository repository;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    repository = MockAuthRepository();
    when(repository.isAuthenticated()).thenAnswer((_) async => false);
  });

  test('startup leaves checking state when redirect recovery hangs', () async {
    final provider = _provider(
      repository: repository,
      google: _FakeGoogleSignInService(
        redirectResult: Completer<String?>().future,
      ),
    );

    expect(provider.isCheckingAuth, isTrue);
    await Future<void>.delayed(const Duration(milliseconds: 30));

    expect(provider.isCheckingAuth, isFalse);
    expect(provider.errorMessage, isNull);
    provider.dispose();
  });

  test('Google cancellation is visible and clears loading', () async {
    final provider = _provider(
      repository: repository,
      google: _FakeGoogleSignInService(error: 'popup-closed-by-user'),
    );
    await Future<void>.delayed(const Duration(milliseconds: 1));

    await provider.signInWithGoogle();

    expect(provider.isLoading, isFalse);
    expect(provider.errorMessage, 'Đăng nhập bằng Google đã bị hủy.');
    provider.dispose();
  });

  test(
    'Firebase unavailable keeps email auth available with clear OAuth error',
    () async {
      final provider = _provider(
        repository: repository,
        google: _FakeGoogleSignInService(
          error: 'Firebase service is unavailable. Please check configuration.',
        ),
        facebook: _FakeFacebookSignInService(
          error: Exception('Firebase service is unavailable.'),
        ),
      );
      await Future<void>.delayed(const Duration(milliseconds: 1));

      await provider.signInWithGoogle();
      expect(provider.errorMessage, contains('Firebase chưa sẵn sàng'));
      expect(provider.isLoading, isFalse);

      await provider.signInWithFacebook();
      expect(provider.errorMessage, contains('Firebase chưa sẵn sàng'));
      expect(provider.isLoading, isFalse);
      provider.dispose();
    },
  );

  test(
    'email login exposes loading, network failure, and supports retry',
    () async {
      final first = Completer<Either<Failure, UserEntity>>();
      var calls = 0;
      when(
        repository.login(
          email: anyNamed('email'),
          password: anyNamed('password'),
        ),
      ).thenAnswer((_) {
        calls += 1;
        if (calls == 1) {
          return first.future;
        }
        return Future.value(
          const Left(ServerFailure('ClientException: Failed to fetch')),
        );
      });
      final provider = _provider(
        repository: repository,
        google: _FakeGoogleSignInService(),
      );
      await Future<void>.delayed(const Duration(milliseconds: 1));

      final attempt = provider.signInWithEmailPassword(
        'user@example.com',
        'Bad!Pass9',
      );
      expect(provider.isLoading, isTrue);
      first.complete(
        const Left(ServerFailure('ClientException: Failed to fetch')),
      );
      await attempt;
      expect(provider.isLoading, isFalse);
      expect(provider.errorMessage, isNotNull);
      expect(provider.errorMessage, isNot(contains('ClientException')));

      await provider.signInWithEmailPassword('user@example.com', 'Bad!Pass9');
      expect(calls, 2);
      expect(provider.isLoading, isFalse);
      provider.dispose();
    },
  );
}
