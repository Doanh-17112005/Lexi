from collections import Counter
from copy import deepcopy

import pytest

from app.core.cefr_vocabulary_data import (
    CEFR_LEVELS,
    CEFR_VOCABULARY,
    PARTS_OF_SPEECH,
    PROVENANCE_AI_GENERATED,
    PROVENANCE_SOURCE_VERIFIED,
    QA_STATUS_NEEDS_REVIEW,
    QA_STATUS_VERIFIED,
    validate_cefr_vocabulary,
)


def test_seed_has_thirty_structurally_valid_entries_per_cefr_level() -> None:
    validate_cefr_vocabulary()
    counts = Counter(item["level"] for item in CEFR_VOCABULARY)
    assert counts == Counter({level: 30 for level in CEFR_LEVELS})
    assert all(item["definition"] != item["meaning"] for item in CEFR_VOCABULARY)
    assert all(item["part_of_speech"] in PARTS_OF_SPEECH for item in CEFR_VOCABULARY)


def test_seed_natural_keys_are_unique_for_idempotent_upsert() -> None:
    natural_keys = [item["word"].strip().casefold() for item in CEFR_VOCABULARY]
    assert len(natural_keys) == len(set(natural_keys)) == 180


def test_every_entry_has_meaning_definition_and_contextual_example() -> None:
    for item in CEFR_VOCABULARY:
        assert item["meaning"].strip()
        assert len(item["definition"].split()) >= 3
        assert len(item["example"].split()) >= 4


def test_a1_bad_entry_does_not_mix_in_the_a2_low_quality_sense() -> None:
    item = next(item for item in CEFR_VOCABULARY if item["word"] == "bad")

    assert item["definition"] == "Unpleasant and causing difficulties."
    assert item["example"] == "The weather is bad today."


def test_a2_replacements_use_verified_a2_senses() -> None:
    expected = {
        "accident": (
            "An unexpected event that causes damage or injury.",
            "tai nạn",
            "noun",
            "He was injured in a car accident.",
        ),
        "adventure": (
            "An unusual and exciting experience that may involve danger.",
            "chuyến phiêu lưu",
            "noun",
            "Our camping trip became an exciting adventure.",
        ),
        "advertisement": (
            "A picture, film, or text that tries to persuade people to buy something.",
            "bài quảng cáo, quảng cáo",
            "noun",
            "I saw an advertisement for the new cafe.",
        ),
        "airport": (
            "A place where aircraft regularly take off and land, with buildings for passengers to wait in.",
            "sân bay",
            "noun",
            "We arrived at the airport two hours before our flight.",
        ),
        "almost": (
            "Nearly but not completely.",
            "gần như",
            "adverb",
            "The bus was almost empty.",
        ),
        "receive": (
            "To get or be given something.",
            "nhận được",
            "verb",
            "I received an email from my teacher.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    assert not {
        "choose",
        "delicious",
        "different",
        "difficult",
        "message",
        "weather",
    } & by_word.keys()
    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "A2"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW

    assert by_word["already"]["definition"] == "Before the present time."


def test_b1_first_batch_uses_evidenced_b1_senses() -> None:
    expected = {
        "achievement": (
            "A successful result that required considerable effort.",
            "thành tích",
            "noun",
            "Finishing the course was a great achievement.",
        ),
        "behaviour": (
            "The way a person acts.",
            "hành vi, cách cư xử",
            "noun",
            "His calm behaviour helped the group.",
        ),
        "communication": (
            "The act of sharing information with other people.",
            "sự giao tiếp, liên lạc",
            "noun",
            "Good communication between teachers and parents is important.",
        ),
        "confident": (
            "Sure that you can do things well.",
            "tự tin",
            "adjective",
            "She felt confident before the presentation.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    assert not {"advice", "community", "confidence"} & by_word.keys()
    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "B1"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_b1_second_batch_uses_evidenced_b1_senses() -> None:
    expected = {
        "application": (
            "An official request for something, usually made in writing.",
            "đơn xin",
            "noun",
            "She sent her job application yesterday.",
        ),
        "independent": (
            "Able to act or live without help from others.",
            "tự lập, không phụ thuộc",
            "adjective",
            "University taught him to be more independent.",
        ),
        "relationship": (
            "The way two people feel and behave towards each other.",
            "mối quan hệ",
            "noun",
            "Trust is important in any relationship.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    assert "available" not in by_word
    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "B1"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_b1_third_batch_uses_evidenced_b1_senses() -> None:
    expected = {
        "afford": (
            "To have enough money to buy something.",
            "đủ khả năng chi trả",
            "verb",
            "We cannot afford a new car.",
        ),
        "announce": (
            "To make something known publicly or officially.",
            "công bố",
            "verb",
            "They announced the results yesterday.",
        ),
        "avoid": (
            "To stay away from someone or something.",
            "tránh",
            "verb",
            "Try to avoid the city centre during rush hour.",
        ),
        "develop": (
            "To grow or cause something to become more advanced.",
            "phát triển",
            "verb",
            "The course helped her develop her skills.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    assert "describe" not in by_word
    assert "prefer" not in by_word
    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "B1"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_b2_first_batch_uses_evidenced_b2_senses() -> None:
    expected = {
        "beneficial": (
            "Helpful, useful, or having a good effect.",
            "có ích, có lợi",
            "adjective",
            "Regular exercise is beneficial to your health.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    assert "collaborate" not in by_word
    assert by_word["beneficial"]["phonetic"] == "/ˌben.ɪˈfɪʃ.əl/"
    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "B2"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_b2_second_batch_uses_evidenced_b2_senses() -> None:
    expected = {
        "crucial": (
            "Extremely important or necessary.",
            "rất quan trọng, thiết yếu",
            "adjective",
            "Accurate data is crucial to the project's success.",
        ),
        "adequate": (
            "Enough or satisfactory for a particular purpose.",
            "đủ, phù hợp",
            "adjective",
            "The room provides adequate space for the meeting.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    assert "issue" not in by_word
    assert "reliable" not in by_word
    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "B2"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_b2_third_batch_keeps_examples_and_definitions_in_b2_senses() -> None:
    expected = {
        "contribute": (
            "To give something that helps achieve a result.",
            "đóng góp",
            "verb",
            "Everyone contributed ideas to the discussion.",
        ),
        "demonstrate": (
            "To show or make something clear.",
            "chứng minh, minh họa",
            "verb",
            "The experiment demonstrates the effect of heat on metal.",
        ),
        "establish": (
            "To start a company or organisation that will continue for a long time.",
            "thành lập, thiết lập",
            "verb",
            "The university established a new research centre.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "B2"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_c1_first_batch_uses_evidenced_c1_senses() -> None:
    expected = {
        "articulate": (
            "Able to express ideas clearly and effectively.",
            "có khả năng diễn đạt rõ ràng",
            "adjective",
            "She is an articulate advocate for educational reform.",
        ),
        "corruption": (
            "Dishonest or illegal behaviour, especially by people in positions of power.",
            "sự tham nhũng",
            "noun",
            "The investigation uncovered widespread corruption.",
        ),
        "counterpart": (
            "A person or thing with the same purpose as another in a different place or organisation.",
            "người hoặc vật tương ứng",
            "noun",
            "The minister met her European counterparts.",
        ),
        "comparable": (
            "Similar in size, amount, or quality to something else.",
            "có thể so sánh",
            "adjective",
            "The two studies produced comparable results.",
        ),
        "implication": (
            "A possible effect that an action or decision may have in the future.",
            "hệ quả, tác động có thể có",
            "noun",
            "The discovery has important implications for public health.",
        ),
        "innovation": (
            "A new idea, method, or product.",
            "sáng kiến, sự đổi mới",
            "noun",
            "The new battery design is a major innovation.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    assert {"ambiguity", "coherence", "discrepancy"}.isdisjoint(by_word)
    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "C1"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_c1_second_batch_uses_evidenced_c1_senses() -> None:
    expected = {
        "compelling": (
            "So strong that it makes you believe or accept it.",
            "có sức thuyết phục",
            "adjective",
            "The author presents a compelling case for reform.",
        ),
        "allegation": (
            "A statement made without proof that someone has done something wrong or illegal.",
            "cáo buộc chưa được chứng minh",
            "noun",
            "The company denied allegations of illegal payments.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    assert "intrinsic" not in by_word
    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "C1"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_c1_third_batch_uses_evidenced_c1_senses() -> None:
    expected = {
        "profound": (
            "Very great or intense.",
            "sâu sắc",
            "adjective",
            "The invention had a profound effect on modern life.",
        ),
        "reluctant": (
            "Not willing to do something and therefore slow to do it.",
            "miễn cưỡng, không sẵn lòng",
            "adjective",
            "She was reluctant to discuss the problem in public.",
        ),
        "enforce": (
            "To make people obey a law or rule.",
            "thi hành, buộc tuân thủ",
            "verb",
            "The authorities must enforce the new safety regulations.",
        ),
        "reinforce": (
            "To provide more proof or support for an idea or opinion.",
            "củng cố, làm tăng sức thuyết phục",
            "verb",
            "The latest results reinforce our earlier conclusion.",
        ),
        "eligible": (
            "Having the necessary qualities or satisfying the necessary conditions.",
            "đủ điều kiện, có đủ tư cách",
            "adjective",
            "Only residents over 18 are eligible to vote.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    assert {"arbitrary", "infer", "substantiate"}.isdisjoint(by_word)
    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "C1"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_c2_first_batch_uses_evidenced_senses_without_verifying() -> None:
    expected = {
        "anachronism": (
            "A person, thing, or idea that exists out of its time in history.",
            "người, vật hoặc ý tưởng lỗi thời, sai niên đại",
            "noun",
            "The manual filing system is an anachronism in a digital office.",
        ),
        "equivocal": (
            "Unclear and able to be understood in two different ways.",
            "mơ hồ, nước đôi",
            "adjective",
            "His equivocal response failed to reassure the committee.",
        ),
        "meticulous": (
            "Very careful and with great attention to every detail.",
            "tỉ mỉ, kỹ lưỡng",
            "adjective",
            "The editor was meticulous about punctuation and tone.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    assert "fastidious" not in by_word
    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "C2"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_c2_second_batch_uses_evidenced_senses_without_verifying() -> None:
    expected = {
        "ineffable": (
            "Causing so much emotion that it cannot be described in words.",
            "không thể diễn tả thành lời",
            "adjective",
            "The music evoked an ineffable sense of loss.",
        ),
        "obfuscate": (
            "To make something less clear and harder to understand, especially intentionally.",
            "làm mơ hồ, khiến khó hiểu",
            "verb",
            "Technical jargon can obfuscate an otherwise simple argument.",
        ),
        "parsimonious": (
            "Small in size or amount.",
            "ít ỏi, eo hẹp",
            "adjective",
            "A parsimonious budget left no room for staff training.",
        ),
        "pernicious": (
            "Having a very harmful effect or influence.",
            "rất có hại, gây ảnh hưởng nguy hại",
            "adjective",
            "Misinformation can have a pernicious influence on public debate.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "C2"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_c2_third_batch_uses_evidenced_senses_without_verifying() -> None:
    expected = {
        "sycophant": (
            "A person who praises powerful or rich people insincerely to gain an advantage.",
            "kẻ xu nịnh",
            "noun",
            "The ruler surrounded himself with sycophants who never disagreed.",
        ),
        "vitriolic": (
            "Full of violent hate and anger.",
            "đầy hằn học, cay độc",
            "adjective",
            "The debate descended into vitriolic personal attacks.",
        ),
        "perspicacious": (
            "Quick to notice, understand, or judge things accurately.",
            "nhạy bén, sáng suốt",
            "adjective",
            "His perspicacious analysis anticipated the political shift.",
        ),
    }
    by_word = {item["word"]: item for item in CEFR_VOCABULARY}

    for word, (definition, meaning, part_of_speech, example) in expected.items():
        item = by_word[word]
        assert (
            item["definition"],
            item["meaning"],
            item["part_of_speech"],
            item["example"],
        ) == (definition, meaning, part_of_speech, example)
        assert item["level"] == "C2"
        assert item["provenance_type"] == PROVENANCE_AI_GENERATED
        assert item["qa_status"] == QA_STATUS_NEEDS_REVIEW


def test_unsourced_ai_content_is_never_marked_verified() -> None:
    assert all(
        item["provenance_type"] == PROVENANCE_AI_GENERATED
        and item["source_reference"] is None
        and item["qa_status"] == QA_STATUS_NEEDS_REVIEW
        for item in CEFR_VOCABULARY
    )


def test_validator_rejects_ai_content_marked_verified() -> None:
    items = deepcopy(CEFR_VOCABULARY)
    items[0]["qa_status"] = QA_STATUS_VERIFIED

    with pytest.raises(ValueError, match="AI-generated|source evidence"):
        validate_cefr_vocabulary(items)


def test_validator_requires_reference_for_source_verified_content() -> None:
    items = deepcopy(CEFR_VOCABULARY)
    items[0]["provenance_type"] = PROVENANCE_SOURCE_VERIFIED

    with pytest.raises(ValueError, match="lacks a reference"):
        validate_cefr_vocabulary(items)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("level", "B9", "exactly 30 words"),
        ("part_of_speech", "article", "Unsupported part of speech"),
        ("example", "Too short.", "Example is too short"),
        ("meaning", "ngh\ufffda", "Possible mojibake"),
    ],
)
def test_validator_rejects_machine_detectable_content_errors(field, value, message) -> None:
    items = deepcopy(CEFR_VOCABULARY)
    items[0][field] = value

    with pytest.raises(ValueError, match=message):
        validate_cefr_vocabulary(items)
