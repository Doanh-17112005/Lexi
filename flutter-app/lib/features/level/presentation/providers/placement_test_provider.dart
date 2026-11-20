import 'dart:async';

import 'package:flutter/material.dart';
import 'package:lexilingo_app/core/services/user_scope_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../data/datasources/proficiency_data_source.dart';

/// Provider for managing 6-skill placement test state, resume, and idempotent submission.
class PlacementTestProvider with ChangeNotifier {
  static const String _activeAttemptBaseKey = 'active_placement_attempt_id_v1';

  final ProficiencyDataSource _dataSource;
  final Future<SharedPreferences> Function() _prefsFactory;

  PlacementTestProvider({
    required ProficiencyDataSource dataSource,
    Future<SharedPreferences> Function()? prefsFactory,
  }) : _dataSource = dataSource,
       _prefsFactory = prefsFactory ?? SharedPreferences.getInstance;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  bool _isSubmitting = false;
  bool get isSubmitting => _isSubmitting;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  String? _attemptId;
  String? get attemptId => _attemptId;

  String? _disclaimer;
  String? get disclaimer => _disclaimer;

  List<String> _skills = const [];
  List<String> get skills => _skills;

  List<Map<String, dynamic>> _questions = [];
  List<Map<String, dynamic>> get questions => _questions;

  Map<String, Map<String, dynamic>> _draftAnswers = {};
  Map<String, Map<String, dynamic>> get draftAnswers => _draftAnswers;

  Map<String, dynamic>? _result;
  Map<String, dynamic>? get result => _result;

  String? _submitIdempotencyKey;

  int get answeredCount {
    var count = 0;
    for (final q in _questions) {
      final tid = q['id']?.toString() ?? '';
      if (_isTaskAnswered(q, _draftAnswers[tid])) {
        count++;
      }
    }
    return count;
  }

  static bool _isTaskAnswered(
    Map<String, dynamic> task,
    Map<String, dynamic>? answer,
  ) {
    if (answer == null) return false;
    final taskType = task['task_type']?.toString() ?? 'mcq';
    if (taskType == 'speaking_rubric' || taskType == 'writing_rubric') {
      final text = answer['text_response']?.toString().trim() ?? '';
      return text.isNotEmpty;
    }
    return answer['selected_option'] != null;
  }

  /// Start a fresh 6-skill attempt or resume an existing in-progress attempt.
  Future<void> loadTest({bool forceNew = false}) async {
    _isLoading = true;
    _errorMessage = null;
    _result = null;
    notifyListeners();

    try {
      final prefs = await _prefsFactory();
      final scope = await UserScopeService.getScopeOrDefault();
      final attemptKey = '${_activeAttemptBaseKey}_$scope';

      if (!forceNew) {
        final storedAttemptId = prefs.getString(attemptKey);
        if (storedAttemptId != null && storedAttemptId.isNotEmpty) {
          try {
            final existing = await _dataSource.getSixSkillAttempt(
              storedAttemptId,
            );
            if (existing['status'] == 'in_progress') {
              _attemptId = storedAttemptId;
              _submitIdempotencyKey = 'placement_$storedAttemptId';
              _disclaimer = existing['disclaimer'] as String?;
              _skills = List<String>.from(existing['skills'] ?? const []);
              _questions = List<Map<String, dynamic>>.from(
                existing['questions'] ?? const [],
              );
              final rawSaved = existing['saved_answers'];
              _draftAnswers = {};
              if (rawSaved is Map) {
                rawSaved.forEach((k, v) {
                  if (v is Map) {
                    _draftAnswers[k.toString()] = Map<String, dynamic>.from(v);
                  }
                });
              }
              _errorMessage = null;
              return;
            } else {
              await prefs.remove(attemptKey);
            }
          } catch (_) {
            await prefs.remove(attemptKey);
          }
        }
      } else {
        await prefs.remove(attemptKey);
      }

      final response = await _dataSource.startSixSkillPlacementTest();
      _attemptId = response['attempt_id']?.toString();
      if (_attemptId != null && _attemptId!.isNotEmpty) {
        await prefs.setString(attemptKey, _attemptId!);
        _submitIdempotencyKey = 'placement_$_attemptId';
      }
      _disclaimer = response['disclaimer'] as String?;
      _skills = List<String>.from(response['skills'] ?? const []);
      _questions = List<Map<String, dynamic>>.from(
        response['questions'] ?? const [],
      );
      _draftAnswers = {};
      _errorMessage = null;
    } catch (e) {
      _errorMessage = 'Failed to load placement test: ${e.toString()}';
      _questions = [];
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Record answer locally and persist draft to backend best-effort.
  Future<void> saveAnswer({
    required String taskId,
    int? selectedOption,
    String? textResponse,
  }) async {
    _draftAnswers[taskId] = {
      if (selectedOption != null) 'selected_option': selectedOption,
      if (textResponse != null) 'text_response': textResponse,
    };
    notifyListeners();

    final attemptId = _attemptId;
    if (attemptId == null || attemptId.isEmpty) return;
    try {
      await _dataSource.saveSixSkillAnswer(
        attemptId: attemptId,
        taskId: taskId,
        selectedOption: selectedOption,
        textResponse: textResponse,
      );
    } catch (_) {
      // Draft remains in memory and will still be included in final submit payload.
    }
  }

  /// Submit 6-skill placement test once with duplicate-submit guard & idempotency key.
  Future<bool> submitSixSkillTest(int timeTakenSeconds) async {
    if (_isSubmitting) return false;
    final attemptId = _attemptId;
    if (attemptId == null || attemptId.isEmpty) {
      _errorMessage = 'Placement session missing; please retry.';
      notifyListeners();
      return false;
    }

    _isSubmitting = true;
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final payloadAnswers = _questions
          .map((q) {
            final tid = q['id'].toString();
            final ans = _draftAnswers[tid] ?? const {};
            return <String, dynamic>{
              'task_id': tid,
              if (ans['selected_option'] != null)
                'selected_option': ans['selected_option'],
              if (ans['text_response'] != null)
                'text_response': ans['text_response'],
            };
          })
          .toList();

      final response = await _dataSource.submitSixSkillPlacementTest(
        attemptId: attemptId,
        answers: payloadAnswers,
        timeTakenSeconds: timeTakenSeconds,
        idempotencyKey: _submitIdempotencyKey ?? 'placement_$attemptId',
      );
      _result = response;
      _errorMessage = null;

      final prefs = await _prefsFactory();
      final scope = await UserScopeService.getScopeOrDefault();
      final attemptKey = '${_activeAttemptBaseKey}_$scope';
      await prefs.remove(attemptKey);

      return true;
    } catch (e) {
      _errorMessage = 'Failed to submit test: ${e.toString()}';
      return false;
    } finally {
      _isSubmitting = false;
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Reset provider state for retake.
  void reset() {
    _attemptId = null;
    _disclaimer = null;
    _skills = const [];
    _questions = [];
    _draftAnswers = {};
    _result = null;
    _errorMessage = null;
    _isLoading = false;
    _isSubmitting = false;
    _submitIdempotencyKey = null;
    notifyListeners();
  }
}
