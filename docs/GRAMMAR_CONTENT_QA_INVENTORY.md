# LexiLingo CEFR A1–C2 Grammar & Course Content QA Inventory

**Audit Date:** 2026-11-19  
**Auditor Role:** `@content_grammar` (Learning Content QA)  
**Source Modules Audited:**
- `backend-service/app/core/grammar_course_data.py`
- `backend-service/scripts/seed_grammar_courses.py`
- `backend-service/tests/test_grammar_course_seed_and_uat.py`

---

## 1. Executive Summary & Database Eligibility

| Metric | Count | Status |
|---|---:|---|
| CEFR Courses (`A1`–`C2`) | 6 | Audited & Validated |
| Units (6 Unit 1 Core + 6 Unit 2 Grammar) | 12 | Audited & Validated |
| Grammar Items (`GrammarItem`) | 12 | Audited & Validated |
| Lessons (6 Lesson 1 Starter + 12 Grammar Lessons) | 18 | Audited & Validated |
| Grammar Lesson Exercises (`easy`: 24, `medium`: 24, `hard`: 24) | 72 | Audited & Disambiguated |
| Unit 1 Starter Exercises (`BASE_CEFR_COURSES`) | 12 | Audited & Validated |
| Question Bank Items (`QuestionItem`, 3 tiers × 12 grammar items) | 36 | Audited & Disambiguated |
| **Provenance (`provenance_type`)** | **100% `AI_GENERATED`** | Preserved (no false `VERIFIED` claims) |
| **Editorial QA Status (`qa_status`)** | **100% `NEEDS_REVIEW`** | Eligible for isolated/local seeding only as `NEEDS_REVIEW` |

### Provenance & Editorial QA Policy
- All 12 `GrammarItem` records, 12 Grammar `Lesson` payloads (`Lesson.content["metadata"]`), and 36 `QuestionItem` records explicitly carry:
  - `provenance_type`: `AI_GENERATED` (`provenance:ai_generated` tag)
  - `qa_status`: `NEEDS_REVIEW` (`qa_status:needs_review` tag)
  - `source_reference`: `None` (pending human editorial review / textbook citation before promotion to `VERIFIED`)
- **No items were promoted to `VERIFIED`**, complying strictly with editorial provenance integrity.

---

## 2. Content & Validator Fixes Applied During This Audit

All 15 defects/ambiguities below were identified during line-by-line review and fixed in `backend-service/app/core/grammar_course_data.py`:

| Target ID / Component | Issue Found | Fix Applied |
|---|---|---|
| `_MOJIBAKE_MARKERS` (validator) | Standalone `"Â"` and `"Ã"` caused false-positive failure when checking `grammar.content` / `grammar.summary` (e.g. Vietnamese `"ÂM phụ âm"`). | Narrowed markers to real UTF-8-as-Latin-1 sequences (`\ufffd`, `Ã¡`, `Ã¢`, `Ãª`, `Ã´`, `Ãº`, `Ä‘`, `áº`, `á»`, `Â\xa0`, `â€`) and extended mojibake checks to `grammar.summary`, `grammar.content`, and all `question_bank` prompts/explanations. |
| `validate_grammar_course_catalog()` | Did not verify duplicate option strings or tier-to-`difficulty`/`points` parity. | Added uniqueness checks for `options` in exercises and `question_bank`, plus numeric `difficulty` and `points` parity checks per `difficulty_tier`. |
| `a1_g1_ex3` (fill_blank) | Prompt omitted target verb (`'study'`), leaving `'learns'`/`'practices'` plausible if hint wasn't opened. | Specified `"using 'study'"` directly in the question prompt. |
| `a1_g1_ex6` (fill_blank) | Prompt (`Where {blank} your cousins live?`) lacked tense framing to rule out `'did'`. | Clarified `"Complete the Present Simple question:"` in the prompt. |
| `a2_g1_ex6` (fill_blank) | Prompt (`Why {blank} they at the station on time?`) lacked a past marker, making `'aren't'` valid. | Added `"Past Simple"` and `"yesterday"` so only `'weren't'` is valid. |
| `a2_g2_ex5` (distractor 3) | Distractor `"more clear"` could spark prescriptive-vs-descriptive debate for 1-syllable comparison. | Replaced distractor with `"more clearer"` (clear double-comparison error). |
| `a2_g2` QB3 (distractor 3) | Distractor `"more light"` replaced with unambiguous error. | Replaced distractor with `"lightest than"`. |
| `b1_g2_ex4` (fill_blank) | Prompt omitted verb `'read'` (only in hint), allowing `'follows'`/`'checks'`. | Added `"using/form of 'read'"` directly in prompt. |
| `b2_g1_ex3` (fill_blank) | Prompt omitted verb `'verify'` (only in hint), allowing `'checked'`/`'approved'`. | Added `"using 'verify'"` directly in prompt. |
| `b2_g2_ex3` (fill_blank) | Informal English permits `'was'` with `'our office'` in Type 2 conditionals. | Explicitly specified `"formal Second Conditional with 'be'"` so `'were'` is unambiguous. |
| `c1_g2` QB2 (distractor 4) | `"Having published last spring, readers praised..."` had semantic ambiguity on whether readers published. | Changed to `"Having published last spring, the handbook received praise."` (clear dangling active participle). |
| `c2_g2_ex3` (fill_blank) | Without hint, `'Despite'` would also fit `'... the substantial variance'`. | Added `"(not 'Despite')"` in the prompt so `'Notwithstanding'` is unambiguous. |
| `c2_g2_ex4` (distractor 3) | `"Albeit the blunt language..."` was less clear-cut than testing the finite-clause prohibition taught in theory. | Changed distractor to `"Albeit she used blunt language, her critique was fair."` (explicit `albeit + S + V` error). |
| `c2_g2` QB1 (options) | `"although"` in reduced concessive phrase could be accepted in some informal styles. | Replaced `"although"` distractor with `"despite"` so `"albeit"` is uniquely valid. |
| `c2_g2` QB2 & QB3 (distractors) | QB2 `"lest the auditor requests"` (BrE indicative) and QB3 `"Notwithstanding that..."` (archaic/legal) risked dialect/register ambiguity. | Updated QB2 distractor to `"lest the auditor will request proof"` and QB3 distractor to `"Notwithstanding of the smaller budget, output rose."`. |

---

## 3. Course & Unit Inventory (6 Courses, 12 Units, 18 Lessons)

### 3.1 Base Courses & Unit 1 Starter Lessons (`BASE_CEFR_COURSES`)
*Note: `seed_grammar_courses.py` only inserts Unit 1 + Lesson 1 when `existing_units_count == 0` (e.g., fresh `lexilingo_test`), preserving any pre-existing Unit 1 / Lesson 1 rows in live databases.*

| CEFR | Course Title | Unit 1 Title | Lesson 1 Title | Starter Exercises | Audit Status | Provenance / QA |
|---|---|---|---|---:|---|---|
| A1 | `A1 - English Foundations` | `Unit 1: A1 Core Skills` | `Lesson 1: A1 Mastery Challenge` | 2 (`a1_ex_1` MC, `a1_ex_2` FB) | PASS | `AI_GENERATED` / `NEEDS_REVIEW` |
| A2 | `A2 - Daily Communication` | `Unit 1: A2 Core Skills` | `Lesson 1: A2 Mastery Challenge` | 2 (`a2_ex_1` MC, `a2_ex_2` FB) | PASS | `AI_GENERATED` / `NEEDS_REVIEW` |
| B1 | `B1 - Practical Intermediate` | `Unit 1: B1 Core Skills` | `Lesson 1: B1 Mastery Challenge` | 2 (`b1_ex_1` MC, `b1_ex_2` FB) | PASS | `AI_GENERATED` / `NEEDS_REVIEW` |
| B2 | `B2 - Professional Fluency` | `Unit 1: B2 Core Skills` | `Lesson 1: B2 Mastery Challenge` | 2 (`b2_ex_1` MC, `b2_ex_2` FB) | PASS | `AI_GENERATED` / `NEEDS_REVIEW` |
| C1 | `C1 - Advanced Academic & IELTS` | `Unit 1: C1 Core Skills` | `Lesson 1: C1 Mastery Challenge` | 2 (`c1_ex_1` MC, `c1_ex_2` FB) | PASS | `AI_GENERATED` / `NEEDS_REVIEW` |
| C2 | `C2 - Native Mastery & Nuances` | `Unit 1: C2 Core Skills` | `Lesson 1: C2 Mastery Challenge` | 2 (`c2_ex_1` MC, `c2_ex_2` FB) | PASS | `AI_GENERATED` / `NEEDS_REVIEW` |

### 3.2 Unit 2 Grammar Units, GrammarItems & Grammar Lessons (`GRAMMAR_UNITS_AND_LESSONS`)

| CEFR | Unit 2 Slug | Lesson Slug | GrammarItem Slug & Title | Topic | Exercises (E/M/H) | QB Items (E/M/H) | Audit Status | Provenance / QA |
|---|---|---|---|---|---:|---:|---|---|
| A1 | `unit-a1-grammar` | `a1-grammar-present-simple-to-be` | `grammar-a1-to-be-present-simple`: Verb 'To Be' & Present Simple Habits | `tenses_and_verbs` | 6 (2/2/2) | 3 (1/1/1) | PASS (2 fill-blank prompts disambiguated) | `AI_GENERATED` / `NEEDS_REVIEW` |
| A1 | `unit-a1-grammar` | `a1-grammar-articles-and-nouns` | `grammar-a1-articles-and-plurals`: Articles (a / an / the) & Countable Plurals | `articles_and_nouns` | 6 (2/2/2) | 3 (1/1/1) | PASS | `AI_GENERATED` / `NEEDS_REVIEW` |
| A2 | `unit-a2-grammar` | `a2-grammar-past-simple` | `grammar-a2-past-simple`: Past Simple: Regular, Irregular & Questions | `past_tenses` | 6 (2/2/2) | 3 (1/1/1) | PASS (`a2_g1_ex6` past marker added) | `AI_GENERATED` / `NEEDS_REVIEW` |
| A2 | `unit-a2-grammar` | `a2-grammar-comparatives-and-going-to` | `grammar-a2-comparatives-future-plans`: Comparatives, Superlatives & Future Plans (be going to) | `comparison_and_future` | 6 (2/2/2) | 3 (1/1/1) | PASS (2 distractors tightened) | `AI_GENERATED` / `NEEDS_REVIEW` |
| B1 | `unit-b1-grammar` | `b1-grammar-present-perfect` | `grammar-b1-present-perfect`: Present Perfect vs Past Simple (since / for / already / yet) | `perfect_tenses` | 6 (2/2/2) | 3 (1/1/1) | PASS | `AI_GENERATED` / `NEEDS_REVIEW` |
| B1 | `unit-b1-grammar` | `b1-grammar-first-conditional-and-modals` | `grammar-b1-conditional-1-modals`: First Conditional & Obligation Modals (must / have to) | `conditionals_and_modals` | 6 (2/2/2) | 3 (1/1/1) | PASS (`b1_g2_ex4` verb cue added) | `AI_GENERATED` / `NEEDS_REVIEW` |
| B2 | `unit-b2-grammar` | `b2-grammar-passive-voice` | `grammar-b2-passive-voice`: Passive Voice: Tenses, Modals & Professional Register | `passive_voice` | 6 (2/2/2) | 3 (1/1/1) | PASS (`b2_g1_ex3` verb cue added) | `AI_GENERATED` / `NEEDS_REVIEW` |
| B2 | `unit-b2-grammar` | `b2-grammar-conditionals-2-3-and-contrast` | `grammar-b2-conditionals-2-3-contrast`: Second & Third Conditionals + Contrast Connectors | `conditionals_and_discourse` | 6 (2/2/2) | 3 (1/1/1) | PASS (`b2_g2_ex3` formal subjunctive cue added) | `AI_GENERATED` / `NEEDS_REVIEW` |
| C1 | `unit-c1-grammar` | `c1-grammar-negative-inversion` | `grammar-c1-negative-inversion`: Negative & Restrictive Inversion (Seldom / Not only / Little) | `advanced_syntax` | 6 (2/2/2) | 3 (1/1/1) | PASS | `AI_GENERATED` / `NEEDS_REVIEW` |
| C1 | `unit-c1-grammar` | `c1-grammar-participle-clauses-and-clefts` | `grammar-c1-participle-cleft`: Participle Clauses & Cleft Sentences (It / What) | `cohesion_and_emphasis` | 6 (2/2/2) | 3 (1/1/1) | PASS (QB2 distractor tightened) | `AI_GENERATED` / `NEEDS_REVIEW` |
| C2 | `unit-c2-grammar` | `c2-grammar-inverted-conditionals-subjunctive` | `grammar-c2-inverted-conditionals-subjunctive`: Inverted Conditionals (Were / Had / Should) & Mandative Subjunctive | `subjunctive_and_inversion` | 6 (2/2/2) | 3 (1/1/1) | PASS | `AI_GENERATED` / `NEEDS_REVIEW` |
| C2 | `unit-c2-grammar` | `c2-grammar-concessive-cautionary-structures` | `grammar-c2-albeit-notwithstanding-lest`: Nuanced Concessive & Cautionary Structures (Albeit / Notwithstanding / Lest) | `formal_register_and_nuance` | 6 (2/2/2) | 3 (1/1/1) | PASS (ex3/ex4/QB1-3 tightened) | `AI_GENERATED` / `NEEDS_REVIEW` |

---

## 4. Detailed Item-Level Audit Breakdown (72 Exercises & 36 QuestionBank Items)

### 4.1 Lesson Exercises (72/72 Audited)

| ID | CEFR | Tier | UI Type | Base Type | Correct Answer | Audit Verdict |
|---|---|---|---|---|---|---|
| `a1_g1_ex1` | A1 | easy | `multiple_choice` | `multiple_choice` | `are` | PASS |
| `a1_g1_ex2` | A1 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `a1_g1_ex3` | A1 | medium | `fill_in_the_blank` | `fill_blank` | `studies` | FIXED (added `'study'` cue to prompt) |
| `a1_g1_ex4` | A1 | medium | `dialogue_completion` | `fill_blank` | `don't` | PASS |
| `a1_g1_ex5` | A1 | hard | `grammar_correction` | `fill_blank` | `She doesn't like spicy food.` | PASS |
| `a1_g1_ex6` | A1 | hard | `fill_in_the_blank` | `fill_blank` | `do` | FIXED (specified Present Simple) |
| `a1_g2_ex1` | A1 | easy | `multiple_choice` | `multiple_choice` | `an` | PASS |
| `a1_g2_ex2` | A1 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `a1_g2_ex3` | A1 | medium | `multiple_choice` | `multiple_choice` | `an` | PASS |
| `a1_g2_ex4` | A1 | medium | `fill_in_the_blank` | `fill_blank` | `the` | PASS |
| `a1_g2_ex5` | A1 | hard | `grammar_correction` | `fill_blank` | `She wants to study at a university in Canada.` | PASS |
| `a1_g2_ex6` | A1 | hard | `fill_in_the_blank` | `fill_blank` | `people` | PASS |
| `a2_g1_ex1` | A2 | easy | `multiple_choice` | `multiple_choice` | `visited` | PASS |
| `a2_g1_ex2` | A2 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `a2_g1_ex3` | A2 | medium | `fill_in_the_blank` | `fill_blank` | `bought` | PASS |
| `a2_g1_ex4` | A2 | medium | `dialogue_completion` | `fill_blank` | `was` | PASS |
| `a2_g1_ex5` | A2 | hard | `grammar_correction` | `fill_blank` | `He didn't write any notes during the meeting.` | PASS |
| `a2_g1_ex6` | A2 | hard | `fill_in_the_blank` | `fill_blank` | `weren't` | FIXED (added Past Simple & `yesterday`) |
| `a2_g2_ex1` | A2 | easy | `multiple_choice` | `multiple_choice` | `cleaner` | PASS |
| `a2_g2_ex2` | A2 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `a2_g2_ex3` | A2 | medium | `fill_in_the_blank` | `fill_blank` | `best` | PASS |
| `a2_g2_ex4` | A2 | medium | `collocation_choice` | `multiple_choice` | `more convenient` | PASS |
| `a2_g2_ex5` | A2 | hard | `grammar_correction` | `fill_blank` | `Her explanation is much clearer than the old guide.` | FIXED (distractor `"more clear"` -> `"more clearer"`) |
| `a2_g2_ex6` | A2 | hard | `dialogue_completion` | `fill_blank` | `is going to` | PASS |
| `b1_g1_ex1` | B1 | easy | `multiple_choice` | `multiple_choice` | `for` | PASS |
| `b1_g1_ex2` | B1 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `b1_g1_ex3` | B1 | medium | `fill_in_the_blank` | `fill_blank` | `written` | PASS |
| `b1_g1_ex4` | B1 | medium | `dialogue_completion` | `fill_blank` | `already` | PASS |
| `b1_g1_ex5` | B1 | hard | `grammar_correction` | `fill_blank` | `How long have you known your current manager?` | PASS |
| `b1_g1_ex6` | B1 | hard | `fill_in_the_blank` | `fill_blank` | `yet` | PASS |
| `b1_g2_ex1` | B1 | easy | `multiple_choice` | `multiple_choice` | `will catch` | PASS |
| `b1_g2_ex2` | B1 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `b1_g2_ex3` | B1 | medium | `multiple_choice` | `multiple_choice` | `don't have to` | PASS |
| `b1_g2_ex4` | B1 | medium | `fill_in_the_blank` | `fill_blank` | `reads` | FIXED (added `'read'` cue to prompt) |
| `b1_g2_ex5` | B1 | hard | `grammar_correction` | `fill_blank` | `If it rains tomorrow, the outdoor workshop will move indoors.` | PASS |
| `b1_g2_ex6` | B1 | hard | `fill_in_the_blank` | `fill_blank` | `mustn't` | PASS |
| `b2_g1_ex1` | B2 | easy | `multiple_choice` | `multiple_choice` | `is reviewed` | PASS |
| `b2_g1_ex2` | B2 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `b2_g1_ex3` | B2 | medium | `fill_in_the_blank` | `fill_blank` | `verified` | FIXED (added `'verify'` cue to prompt) |
| `b2_g1_ex4` | B2 | medium | `collocation_choice` | `multiple_choice` | `have been equipped` | PASS |
| `b2_g1_ex5` | B2 | hard | `grammar_correction` | `fill_blank` | `The bridge is being repaired right now, so traffic is diverted.` | PASS |
| `b2_g1_ex6` | B2 | hard | `fill_in_the_blank` | `fill_blank` | `acknowledged` | PASS |
| `b2_g2_ex1` | B2 | easy | `multiple_choice` | `multiple_choice` | `Despite` | PASS |
| `b2_g2_ex2` | B2 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `b2_g2_ex3` | B2 | medium | `fill_in_the_blank` | `fill_blank` | `were` | FIXED (specified formal Second Conditional `'be'`) |
| `b2_g2_ex4` | B2 | medium | `multiple_choice` | `multiple_choice` | `wouldn't have missed` | PASS |
| `b2_g2_ex5` | B2 | hard | `grammar_correction` | `fill_blank` | `If I had known about the cancellation, I wouldn't have travelled downtown.` | PASS |
| `b2_g2_ex6` | B2 | hard | `fill_in_the_blank` | `fill_blank` | `spite` | PASS |
| `c1_g1_ex1` | C1 | easy | `multiple_choice` | `multiple_choice` | `have I witnessed` | PASS |
| `c1_g1_ex2` | C1 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `c1_g1_ex3` | C1 | medium | `fill_in_the_blank` | `fill_blank` | `circumstances` | PASS |
| `c1_g1_ex4` | C1 | medium | `multiple_choice` | `multiple_choice` | `Only after reviewing the logs did the engineers locate the bottleneck.` | PASS |
| `c1_g1_ex5` | C1 | hard | `grammar_correction` | `fill_blank` | `Not until the rain stopped did we resume the excavation.` | PASS |
| `c1_g1_ex6` | C1 | hard | `fill_in_the_blank` | `fill_blank` | `does` | PASS |
| `c1_g2_ex1` | C1 | easy | `multiple_choice` | `multiple_choice` | `Founded` | PASS |
| `c1_g2_ex2` | C1 | easy | `true_or_false` | `true_false` | `True` | PASS |
| `c1_g2_ex3` | C1 | medium | `fill_in_the_blank` | `fill_blank` | `Having` | PASS |
| `c1_g2_ex4` | C1 | medium | `multiple_choice` | `multiple_choice` | `the linguists identified three recurring patterns` | PASS |
| `c1_g2_ex5` | C1 | hard | `grammar_correction` | `fill_blank` | `It was the sudden drop in temperature that halted the outdoor experiment.` | PASS |
| `c1_g2_ex6` | C1 | hard | `fill_in_the_blank` | `fill_blank` | `What` | PASS |
| `c2_g1_ex1` | C2 | easy | `multiple_choice` | `multiple_choice` | `Had the team intervened` | PASS |
| `c2_g1_ex2` | C2 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `c2_g1_ex3` | C2 | medium | `fill_in_the_blank` | `fill_blank` | `release` | PASS |
| `c2_g1_ex4` | C2 | medium | `multiple_choice` | `multiple_choice` | `Were the board to approve` | PASS |
| `c2_g1_ex5` | C2 | hard | `grammar_correction` | `fill_blank` | `It is imperative that the witness not leave before the hearing adjourns.` | PASS |
| `c2_g1_ex6` | C2 | hard | `fill_in_the_blank` | `fill_blank` | `Should` | PASS |
| `c2_g2_ex1` | C2 | easy | `multiple_choice` | `multiple_choice` | `albeit` | PASS |
| `c2_g2_ex2` | C2 | easy | `true_or_false` | `true_false` | `False` | PASS |
| `c2_g2_ex3` | C2 | medium | `fill_in_the_blank` | `fill_blank` | `Notwithstanding` | FIXED (excluded `'Despite'` in prompt) |
| `c2_g2_ex4` | C2 | medium | `multiple_choice` | `multiple_choice` | `Her critique was fair, albeit delivered in blunt language.` | FIXED (distractor 3 changed to `albeit + S + V`) |
| `c2_g2_ex5` | C2 | hard | `grammar_correction` | `fill_blank` | `The committee postponed the vote lest premature rumors destabilize the talks.` | PASS |
| `c2_g2_ex6` | C2 | hard | `collocation_choice` | `multiple_choice` | `though` | PASS |

### 4.2 Question Bank Items (36/36 Audited)

| Lesson Slug | Tier | Answer | Audit Verdict |
|---|---|---|---|
| `a1-grammar-present-simple-to-be` | easy / medium / hard | `They are very friendly neighbors.` / `leaves` / `My brother doesn't watch television.` | 3/3 PASS |
| `a1-grammar-articles-and-nouns` | easy / medium / hard | `an` / `Because the 'h' is silent and it starts with a vowel sound` / `She gave me a useful piece of advice.` | 3/3 PASS |
| `a2-grammar-past-simple` | easy / medium / hard | `took` / `Did` / `Neither of the trains stopped at that small town.` | 3/3 PASS |
| `a2-grammar-comparatives-and-going-to` | easy / medium / hard | `worse` / `She is going to learn Japanese next semester.` / `This tablet is far lighter than my laptop.` | PASS (QB3 distractor tightened) |
| `b1-grammar-present-perfect` | easy / medium / hard | `yet` / `She joined the club two years ago and has stayed active since then.` / `Have you ever attended an international workshop?` | 3/3 PASS |
| `b1-grammar-first-conditional-and-modals` | easy / medium / hard | `leave` / `You don't have to wear a tie.` / `Unless she finishes early, she will miss the last ferry.` | 3/3 PASS |
| `b2-grammar-passive-voice` | easy / medium / hard | `will be sent` / `The solar panels are being installed on the roof today.` / `Three critical bugs were resolved before the release window closed.` | 3/3 PASS |
| `b2-grammar-conditionals-2-3-and-contrast` | easy / medium / hard | `Although` / `If I had more free time, I would practice piano daily.` / `If we hadn't overlooked that clause, we wouldn't face this penalty now.` | 3/3 PASS |
| `c1-grammar-negative-inversion` | easy / medium / hard | `have I` / `No sooner had the panel adjourned than questions poured in.` / `On no account must employees disclose client records.` | 3/3 PASS |
| `c1-grammar-participle-clauses-and-clefts` | easy / medium / hard | `Recognizing` / `Published last spring, the handbook received praise for its clarity.` / `What distinguishes the second cohort is its higher retention rate.` | PASS (QB2 distractor tightened) |
| `c2-grammar-inverted-conditionals-subjunctive` | easy / medium / hard | `Should` / `Had they not secured funding, the clinic would have closed.` / `Regulations demand that every applicant be present for identity verification.` | 3/3 PASS |
| `c2-grammar-concessive-cautionary-structures` | easy / medium / hard | `albeit` / `Keep copies of every receipt lest the auditor request proof.` / `Ambitious though the target may seem, the timeline remains viable.` | PASS (QB1–QB3 distractors tightened) |

---

## 5. Verification Evidence (`lexilingo_test` Only — Live `lexilingo` Untouched)

1. `.\venv\Scripts\python.exe -m scripts.seed_grammar_courses --target test --dry-run`
   - `courses: created=6, updated=0, unchanged=0`
   - `units: created=12, updated=0, unchanged=0`
   - `grammar_items: created=12, updated=0, unchanged=0`
   - `lessons: created=18, updated=0, unchanged=0`
   - `question_bank: created=36, updated=0, unchanged=0`
2. `.\venv\Scripts\python.exe -m scripts.seed_grammar_courses --target test --apply` (Run 1)
   - `courses: created=6, updated=0, unchanged=0`
   - `units: created=12, updated=0, unchanged=0`
   - `grammar_items: created=12, updated=0, unchanged=0`
   - `lessons: created=18, updated=0, unchanged=0`
   - `question_bank: created=36, updated=0, unchanged=0`
3. `.\venv\Scripts\python.exe -m scripts.seed_grammar_courses --target test --apply` (Run 2 — idempotency proof)
   - `courses: created=0, updated=0, unchanged=6`
   - `units: created=0, updated=0, unchanged=6`
   - `grammar_items: created=0, updated=0, unchanged=12`
   - `lessons: created=0, updated=0, unchanged=12`
   - `question_bank: created=0, updated=0, unchanged=36`
4. `.\venv\Scripts\python.exe -m pytest -p no:cacheprovider tests/test_grammar_course_seed_and_uat.py -q`
   - `3 passed in 6.91s` (structure/tiers/provenance, idempotent upsert preserving Lesson 1 & `AI_GENERATED + NEEDS_REVIEW`, no-answer-leak + roadmap unlock + theory-viewed 0 XP + answer scoring + reload persistence).
5. `.\venv\Scripts\python.exe -m ruff check app/core/grammar_course_data.py scripts/seed_grammar_courses.py tests/test_grammar_course_seed_and_uat.py`
   - `All checks passed!`
