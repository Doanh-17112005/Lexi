import 'dart:convert';

import 'package:dartz/dartz.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:lexilingo_app/core/error/failures.dart';
import 'package:lexilingo_app/core/network/api_client.dart';
import 'package:lexilingo_app/core/network/network_info.dart';
import 'package:lexilingo_app/features/vocabulary/data/models/vocabulary_tags.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/user_vocabulary_entity.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/vocab_word.dart';
import 'package:lexilingo_app/features/vocabulary/domain/entities/vocabulary_item_entity.dart';
import 'package:lexilingo_app/features/vocabulary/domain/repositories/vocab_repository.dart';
import 'package:lexilingo_app/features/vocabulary/domain/repositories/vocabulary_repository.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/add_word_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/get_due_vocabulary_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/get_words_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/domain/usecases/submit_review_usecase.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/pages/vocab_library_page.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/providers/flashcard_provider.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/providers/quiz_provider.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/providers/vocab_provider.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/screens/quiz_review_screen.dart';
import 'package:lexilingo_app/features/vocabulary/presentation/widgets/quiz_option_card.dart';
import 'package:lexilingo_app/features/vocabulary/vocabulary_di.dart'
    as vocab_di;
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _AlwaysConnectedNetworkInfo implements NetworkInfo {
  @override
  Future<bool> get isConnected async => true;
}

class _EmptyLocalVocabRepository implements VocabRepository {
  @override
  Future<Either<Failure, void>> addWord(VocabWord word) async =>
      const Right(null);

  @override
  Future<Either<Failure, List<VocabWord>>> getWords() async => const Right([]);
}

class _SeedTopicVocabularyRepository extends Fake
    implements VocabularyRepository {
  final List<VocabularyItemEntity> catalog;
  final List<String?> requestedTags = [];

  _SeedTopicVocabularyRepository(this.catalog);

  @override
  Future<Either<Failure, List<VocabularyItemEntity>>> getVocabularyItems({
    String? courseId,
    String? lessonId,
    String? difficultyLevel,
    String? tag,
    String? search,
    int limit = 50,
    int offset = 0,
  }) async {
    requestedTags.add(tag);
    final canonical = normalizeVocabularyTopic(tag);
    final matched = catalog
        .where(
          (item) =>
              canonical == null ||
              normalizeVocabularyTags(item.tags).contains(canonical),
        )
        .skip(offset)
        .take(limit)
        .toList();
    return Right(matched);
  }

  @override
  Future<Either<Failure, List<UserVocabularyEntity>>> getUserCollection({
    VocabularyStatus? status,
    int limit = 50,
    int offset = 0,
  }) async => const Right([]);

  @override
  Future<Either<Failure, UserVocabularyEntity>> addToCollection(
    String vocabularyId,
  ) async => Right(
    UserVocabularyEntity(
      id: 'uv-$vocabularyId',
      userId: 'user-1',
      vocabularyId: vocabularyId,
      status: VocabularyStatus.learning,
      nextReviewDate: DateTime.utc(2026, 11, 18),
      addedAt: DateTime.utc(2026, 11, 18),
    ),
  );
}

class _VocabTestAssetLoader extends AssetLoader {
  const _VocabTestAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
    'common': {
      'retry': 'Retry',
      'cancel': 'Cancel',
      'create': 'Create',
      'delete': 'Delete',
    },
    'vocabulary': {
      'library': 'Vocabulary Library',
      'tabWords': 'Words',
      'tabTopics': 'Topics',
      'searchPlaceholder': 'Search words...',
      'filterAll': 'All',
      'recentWordsHeader': 'Recent Words',
      'wordCount': '{} words',
      'systemTopicsHeader': 'System Topics',
      'customDecksHeader': 'Custom Decks',
      'createCustomDeck': 'Create Deck',
      'startLearning': 'Start',
      'noDefinitionYet': 'No definition yet',
      'topicGeneral': 'General',
      'topicGeneralSubtitle': 'Core everyday words',
      'topicTravel': 'Travel',
      'topicTravelSubtitle': 'Trips & transport',
      'topicBusiness': 'Business',
      'topicBusinessSubtitle': 'Work & meetings',
      'topicDailyLife': 'Daily Life',
      'topicDailyLifeSubtitle': 'Routines & home',
      'topicScience': 'Science',
      'topicScienceSubtitle': 'Research & discovery',
      'topicTechnology': 'Technology',
      'topicTechnologySubtitle': 'Digital & software',
    },
    'vocabQuiz': {
      'chooseMode': 'Choose study mode',
      'modeQuizTitle': 'Quiz Mode',
      'modeQuizSubtitle': 'Multiple-choice practice',
      'modeFlashcardTitle': 'Flashcards',
      'modeFlashcardSubtitle': 'Flip cards with SRS',
      'empty': 'Empty',
      'term': 'Term',
      'chooseCorrect': 'Choose the matching definition',
    },
  };
}

List<Map<String, dynamic>> _seedPayloads() => [
  {
    'id': 'v-1',
    'word': 'articulate',
    'definition': 'Able to express ideas clearly.',
    'difficulty_level': 'C1',
    'tags': {
      'source': 'AI_GENERATED',
      'qa_status': 'NEEDS_REVIEW',
      'topic': ['general'],
    },
  },
  {
    'id': 'v-2',
    'word': 'airport',
    'definition': 'A place where aircraft take off and land.',
    'difficulty_level': 'A2',
    'tags': {
      'source': 'AI_GENERATED',
      'qa_status': 'NEEDS_REVIEW',
      'topic': ['travel'],
    },
  },
  {
    'id': 'v-3',
    'word': 'negotiate',
    'definition': 'To discuss formally to reach agreement.',
    'difficulty_level': 'B2',
    'tags': {
      'source': 'AI_GENERATED',
      'qa_status': 'NEEDS_REVIEW',
      'topic': ['business'],
    },
  },
  {
    'id': 'v-4',
    'word': 'morning',
    'definition': 'The early part of the day before noon.',
    'difficulty_level': 'A1',
    'tags': {
      'source': 'AI_GENERATED',
      'qa_status': 'NEEDS_REVIEW',
      'topic': ['daily_life'],
    },
  },
  {
    'id': 'v-5',
    'word': 'habit',
    'definition': 'Something that you do regularly.',
    'difficulty_level': 'B1',
    'tags': {
      'source': 'AI_GENERATED',
      'qa_status': 'NEEDS_REVIEW',
      'topic': ['daily'],
    },
  },
  {
    'id': 'v-6',
    'word': 'evidence',
    'definition': 'Facts that support a scientific conclusion.',
    'difficulty_level': 'B2',
    'tags': {
      'source': 'AI_GENERATED',
      'qa_status': 'NEEDS_REVIEW',
      'topic': ['science'],
    },
  },
  {
    'id': 'v-7',
    'word': 'innovation',
    'definition': 'A new idea, method, or device.',
    'difficulty_level': 'C1',
    'tags': {
      'source': 'AI_GENERATED',
      'qa_status': 'NEEDS_REVIEW',
      'topic': ['technology'],
    },
  },
];

List<VocabularyItemEntity> _seedEntities() => _seedPayloads()
    .map(
      (raw) => VocabularyItemEntity(
        id: raw['id'] as String,
        word: raw['word'] as String,
        definition: raw['definition'] as String,
        partOfSpeech: 'noun',
        difficultyLevel: raw['difficulty_level'] as String,
        tags: normalizeVocabularyTags(raw['tags']),
        createdAt: DateTime.utc(2026, 11, 18),
      ),
    )
    .toList();

VocabProvider _createSeedVocabProvider() {
  final payloads = _seedPayloads();
  final apiClient = ApiClient(
    client: MockClient((request) async {
      if (request.url.path == '/vocabulary/collection') {
        return http.Response(
          jsonEncode({'items': [], 'total': 0, 'has_more': false}),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      if (request.url.path == '/vocabulary/decks') {
        return http.Response(
          jsonEncode([]),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      if (request.url.path == '/vocabulary/items') {
        final level = request.url.queryParameters['difficulty_level'];
        final tag = request.url.queryParameters['tag'];
        final filtered = payloads.where((raw) {
          if (level != null && raw['difficulty_level'] != level) return false;
          if (tag != null &&
              !normalizeVocabularyTags(raw['tags']).contains(tag)) {
            return false;
          }
          return true;
        }).toList();
        return http.Response(
          jsonEncode(filtered),
          200,
          headers: {'content-type': 'application/json'},
        );
      }
      return http.Response('Not Found', 404);
    }),
    baseUrl: 'http://test.local',
    networkInfo: _AlwaysConnectedNetworkInfo(),
    enableLogging: false,
  );

  final localRepo = _EmptyLocalVocabRepository();
  return VocabProvider(
    getWordsUseCase: GetWordsUseCase(localRepo),
    addWordUseCase: AddWordUseCase(localRepo),
    apiClient: apiClient,
  );
}

Widget _wrapLibrary({
  required VocabProvider vocabProvider,
  required FlashcardProvider flashcardProvider,
}) {
  return EasyLocalization(
    supportedLocales: const [Locale('en')],
    path: 'assets/i18n',
    fallbackLocale: const Locale('en'),
    startLocale: const Locale('en'),
    useOnlyLangCode: true,
    assetLoader: const _VocabTestAssetLoader(),
    child: MultiProvider(
      providers: [
        ChangeNotifierProvider<VocabProvider>.value(value: vocabProvider),
        ChangeNotifierProvider<FlashcardProvider>.value(
          value: flashcardProvider,
        ),
      ],
      child: Builder(
        builder: (context) => MaterialApp(
          locale: context.locale,
          supportedLocales: context.supportedLocales,
          localizationsDelegates: context.localizationDelegates,
          home: const VocabLibraryPage(),
        ),
      ),
    ),
  );
}

void main() {
  late _SeedTopicVocabularyRepository repo;

  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    SharedPreferences.setMockInitialValues({});
    EasyLocalization.logger.enableLevels = [];
    await EasyLocalization.ensureInitialized();
  });

  setUp(() {
    repo = _SeedTopicVocabularyRepository(_seedEntities());
    if (vocab_di.getIt.isRegistered<QuizProvider>()) {
      vocab_di.getIt.unregister<QuizProvider>();
    }
    vocab_di.getIt.registerFactory<QuizProvider>(
      () => QuizProvider(
        getDueVocabularyUseCase: GetDueVocabularyUseCase(repo),
        submitReviewUseCase: SubmitReviewUseCase(repo),
        vocabularyRepository: repo,
      ),
    );
  });

  tearDown(() {
    if (vocab_di.getIt.isRegistered<QuizProvider>()) {
      vocab_di.getIt.unregister<QuizProvider>();
    }
  });

  testWidgets(
    'Words tab renders canonical topic filter chips and combines topic + CEFR filters',
    (tester) async {
      tester.view.physicalSize = const Size(1080, 1920);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      final vocabProvider = _createSeedVocabProvider();
      final flashcardProvider = FlashcardProvider(
        getDueVocabularyUseCase: GetDueVocabularyUseCase(repo),
        submitReviewUseCase: SubmitReviewUseCase(repo),
        vocabularyRepository: repo,
      );

      await tester.pumpWidget(
        _wrapLibrary(
          vocabProvider: vocabProvider,
          flashcardProvider: flashcardProvider,
        ),
      );
      await tester.pumpAndSettle();

      final horizontalTopicScrollable = find
          .byWidgetPredicate(
            (widget) =>
                widget is Scrollable &&
                widget.axisDirection == AxisDirection.right,
          )
          .last;

      for (final label in [
        'Business',
        'Daily Life',
        'General',
        'Science',
        'Technology',
        'Travel',
      ]) {
        await tester.scrollUntilVisible(
          find.text(label),
          120,
          scrollable: horizontalTopicScrollable,
        );
        expect(find.text(label), findsOneWidget);
      }

      await tester.drag(horizontalTopicScrollable, const Offset(600, 0));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('Daily Life'));
      await tester.tap(find.text('Daily Life'));
      await tester.pumpAndSettle();
      expect(vocabProvider.selectedTag, 'daily');
      expect(find.text('morning'), findsOneWidget);
      expect(find.text('habit'), findsOneWidget);
      expect(find.text('airport'), findsNothing);

      await tester.tap(find.text('B1'));
      await tester.pumpAndSettle();
      expect(vocabProvider.selectedLevel, 'B1');
      expect(find.text('habit'), findsOneWidget);
      expect(find.text('morning'), findsNothing);
    },
  );

  testWidgets(
    'Topics tab renders all 6 system topic cards and launches canonical Quiz session',
    (tester) async {
      tester.view.physicalSize = const Size(1080, 1920);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.reset);

      final vocabProvider = _createSeedVocabProvider();
      final flashcardProvider = FlashcardProvider(
        getDueVocabularyUseCase: GetDueVocabularyUseCase(repo),
        submitReviewUseCase: SubmitReviewUseCase(repo),
        vocabularyRepository: repo,
      );

      await tester.pumpWidget(
        _wrapLibrary(
          vocabProvider: vocabProvider,
          flashcardProvider: flashcardProvider,
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Topics'));
      await tester.pumpAndSettle();

      for (final label in [
        'General',
        'Travel',
        'Business',
        'Daily Life',
        'Science',
        'Technology',
      ]) {
        expect(find.text(label), findsOneWidget);
      }

      await tester.ensureVisible(find.text('Daily Life'));
      await tester.tap(find.text('Daily Life'));
      await tester.pumpAndSettle();

      expect(find.text('Quiz Mode'), findsOneWidget);
      expect(find.text('Flashcards'), findsOneWidget);

      await tester.tap(find.text('Quiz Mode'));
      await tester.pumpAndSettle();

      expect(find.byType(QuizReviewScreen), findsOneWidget);
      expect(find.byType(QuizOptionCard), findsWidgets);
      expect(repo.requestedTags.first, 'daily');
    },
  );
}
