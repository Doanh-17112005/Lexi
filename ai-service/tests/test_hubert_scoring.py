from api.services.hubert_service import HuBERTService


def test_confidence_scores_do_not_invent_vowel_or_consonant_metrics():
    scores = HuBERTService._confidence_scores(0.92)

    assert scores == {"overall_confidence": 0.92}


def test_confidence_scores_are_bounded():
    assert HuBERTService._confidence_scores(1.2) == {"overall_confidence": 1.0}
    assert HuBERTService._confidence_scores(-0.2) == {"overall_confidence": 0.0}
