"""Unverified CEFR seed vocabulary with explicit provenance and QA state."""

import re
from collections import Counter

CEFR_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
PARTS_OF_SPEECH = {"adjective", "adverb", "noun", "preposition", "verb"}
PROVENANCE_AI_GENERATED = "AI_GENERATED"
PROVENANCE_SOURCE_VERIFIED = "SOURCE_VERIFIED"
QA_STATUS_NEEDS_REVIEW = "NEEDS_REVIEW"
QA_STATUS_VERIFIED = "VERIFIED"

_ALLOWED_PROVENANCE_TYPES = {
    PROVENANCE_AI_GENERATED,
    PROVENANCE_SOURCE_VERIFIED,
}
_ALLOWED_QA_STATUSES = {QA_STATUS_NEEDS_REVIEW, QA_STATUS_VERIFIED}
_WORD_PATTERN = re.compile(r"^[a-z]+(?:[-'][a-z]+)*$")
_MOJIBAKE_MARKERS = ("\ufffd", "Ã", "Â", "â€")

# Word, English definition, Vietnamese meaning, part of speech, example.
_ROWS: dict[str, list[tuple[str, str, str, str, str]]] = {
    "A1": [
        ("family", "A group of people who are related to one another.", "gia đình", "noun", "I have dinner with my family every evening."),
        ("happy", "Feeling or showing pleasure.", "vui vẻ, hạnh phúc", "adjective", "She is happy to see her friend."),
        ("house", "A building where people live.", "ngôi nhà", "noun", "Their house has a small garden."),
        ("school", "A place where people go to learn.", "trường học", "noun", "The children walk to school together."),
        ("friend", "A person whom you know and like.", "người bạn", "noun", "My friend lives near the park."),
        ("water", "The clear liquid that people and animals drink.", "nước", "noun", "Please drink some water after the game."),
        ("food", "Things that people or animals eat.", "thức ăn, đồ ăn", "noun", "We buy fresh food at the market."),
        ("morning", "The early part of the day before noon.", "buổi sáng", "noun", "I study English every morning."),
        ("work", "To do a job or an activity that needs effort.", "làm việc", "verb", "My parents work in the city."),
        ("name", "The word used to identify a person or thing.", "tên", "noun", "Please write your name here."),
        ("book", "A set of printed or digital pages containing text.", "quyển sách", "noun", "This book has many pictures."),
        ("city", "A large town where many people live and work.", "thành phố", "noun", "Ho Chi Minh City is very busy."),
        ("mother", "A female parent.", "mẹ", "noun", "Her mother is a teacher."),
        ("father", "A male parent.", "bố, cha", "noun", "His father cooks dinner on Sundays."),
        ("child", "A young person who is not yet an adult.", "đứa trẻ", "noun", "The child is playing with a ball."),
        ("eat", "To put food in your mouth and swallow it.", "ăn", "verb", "We eat lunch at twelve o'clock."),
        ("drink", "To take liquid into your mouth and swallow it.", "uống", "verb", "They drink tea in the morning."),
        ("sleep", "To rest with your eyes closed.", "ngủ", "verb", "I usually sleep for eight hours."),
        ("speak", "To say words using your voice.", "nói", "verb", "Can you speak English?"),
        ("read", "To look at and understand written words.", "đọc", "verb", "He likes to read before bed."),
        ("write", "To make letters or words on a surface.", "viết", "verb", "Write the answer in your notebook."),
        ("big", "Large in size or amount.", "to, lớn", "adjective", "There is a big tree outside."),
        ("small", "Little in size or amount.", "nhỏ", "adjective", "She carries a small bag."),
        ("good", "Pleasant, useful, or of high quality.", "tốt", "adjective", "That is a good idea."),
        ("bad", "Unpleasant and causing difficulties.", "xấu, tệ", "adjective", "The weather is bad today."),
        ("today", "On or during the present day.", "hôm nay", "adverb", "We have an English lesson today."),
        ("tomorrow", "On or during the day after today.", "ngày mai", "adverb", "I will call you tomorrow."),
        ("always", "At all times or every time.", "luôn luôn", "adverb", "He always brushes his teeth after breakfast."),
        ("near", "Not far away in distance.", "gần", "preposition", "The bus stop is near my house."),
        ("beautiful", "Very attractive or pleasant to see.", "đẹp", "adjective", "The beach is beautiful at sunset."),
    ],
    "A2": [
        ("journey", "An act of travelling from one place to another.", "chuyến đi, hành trình", "noun", "The train journey took three hours."),
        ("polite", "Showing good manners and respect for other people.", "lịch sự, lễ phép", "adjective", "It is polite to say thank you."),
        ("arrive", "To reach a place at the end of a journey.", "đến nơi", "verb", "Our bus will arrive at nine."),
        ("borrow", "To take and use something that you will return.", "mượn", "verb", "May I borrow your dictionary?"),
        ("decide", "To choose something after thinking about it.", "quyết định", "verb", "We decided to walk home."),
        ("accident", "An unexpected event that causes damage or injury.", "tai nạn", "noun", "He was injured in a car accident."),
        ("adventure", "An unusual and exciting experience that may involve danger.", "chuyến phiêu lưu", "noun", "Our camping trip became an exciting adventure."),
        ("invitation", "A request asking someone to go somewhere or do something.", "lời mời", "noun", "Thank you for the party invitation."),
        ("market", "A place where people buy and sell things.", "chợ", "noun", "We bought vegetables at the local market."),
        ("advertisement", "A picture, film, or text that tries to persuade people to buy something.", "bài quảng cáo, quảng cáo", "noun", "I saw an advertisement for the new cafe."),
        ("neighbour", "A person who lives near you.", "hàng xóm", "noun", "Our neighbour helped us move the table."),
        ("perhaps", "Used to say that something is possible.", "có lẽ", "adverb", "Perhaps we can meet after lunch."),
        ("prepare", "To make something ready for use or an event.", "chuẩn bị", "verb", "She is preparing food for the trip."),
        ("return", "To go or come back to a place.", "trở về, quay lại", "verb", "They returned home before dark."),
        ("suddenly", "Quickly and unexpectedly.", "đột nhiên", "adverb", "The lights suddenly went out."),
        ("airport", "A place where aircraft regularly take off and land, with buildings for passengers to wait in.", "sân bay", "noun", "We arrived at the airport two hours before our flight."),
        ("afraid", "Feeling fear or worry.", "sợ hãi", "adjective", "The little boy is afraid of dogs."),
        ("careful", "Giving attention so that you avoid mistakes or danger.", "cẩn thận", "adjective", "Be careful when you cross the road."),
        ("comfortable", "Making you feel physically relaxed.", "thoải mái", "adjective", "These shoes are light and comfortable."),
        ("crowded", "Full of people, leaving little space.", "đông đúc", "adjective", "The station was crowded this morning."),
        ("almost", "Nearly but not completely.", "gần như", "adverb", "The bus was almost empty."),
        ("friendly", "Kind and pleasant towards other people.", "thân thiện", "adjective", "The hotel staff were very friendly."),
        ("healthy", "In good physical condition or good for your health.", "khỏe mạnh, lành mạnh", "adjective", "Walking is a healthy daily habit."),
        ("quickly", "At a fast speed or without delay.", "nhanh chóng", "adverb", "Please finish your breakfast quickly."),
        ("already", "Before the present time.", "đã, rồi", "adverb", "I have already finished my homework."),
        ("during", "Throughout or at a point within a period of time.", "trong suốt, trong khi", "preposition", "Nobody spoke during the film."),
        ("without", "Not having or using something.", "không có", "preposition", "He left without his umbrella."),
        ("receive", "To get or be given something.", "nhận được", "verb", "I received an email from my teacher."),
        ("explain", "To make something clear by describing it.", "giải thích", "verb", "Could you explain this word to me?"),
        ("promise", "To say firmly that you will do something.", "hứa", "verb", "I promise to return the book tomorrow."),
    ],
    "B1": [
        ("opportunity", "A situation that makes it possible to do something useful.", "cơ hội", "noun", "The internship is a valuable opportunity to learn."),
        ("convenient", "Suitable for your needs and causing little difficulty.", "thuận tiện", "adjective", "Online booking is fast and convenient."),
        ("achieve", "To succeed in doing something after making an effort.", "đạt được", "verb", "She worked hard to achieve her goal."),
        ("achievement", "A successful result that required considerable effort.", "thành tích", "noun", "Finishing the course was a great achievement."),
        ("behaviour", "The way a person acts.", "hành vi, cách cư xử", "noun", "His calm behaviour helped the group."),
        ("challenge", "A difficult task that tests your ability.", "thử thách", "noun", "Learning to present confidently was a challenge."),
        ("communication", "The act of sharing information with other people.", "sự giao tiếp, liên lạc", "noun", "Good communication between teachers and parents is important."),
        ("confident", "Sure that you can do things well.", "tự tin", "adjective", "She felt confident before the presentation."),
        ("decision", "A choice made after considering several possibilities.", "quyết định", "noun", "Moving abroad was a difficult decision."),
        ("experience", "Knowledge or skill gained by doing something.", "kinh nghiệm", "noun", "She has experience in customer service."),
        ("goal", "Something that you hope to achieve.", "mục tiêu", "noun", "My main goal is to speak more fluently."),
        ("habit", "Something that you do regularly, often without thinking.", "thói quen", "noun", "Reading every day is a useful habit."),
        ("knowledge", "Information and understanding gained through learning.", "kiến thức", "noun", "The course increased my knowledge of history."),
        ("opinion", "A belief or view about something.", "ý kiến, quan điểm", "noun", "In my opinion, public transport should be cheaper."),
        ("relationship", "The way two people feel and behave towards each other.", "mối quan hệ", "noun", "Trust is important in any relationship."),
        ("solution", "An answer to a problem.", "giải pháp", "noun", "We need a practical solution to the traffic problem."),
        ("advantage", "A condition that helps you or makes success more likely.", "lợi thế", "noun", "Speaking two languages is a clear advantage."),
        ("application", "An official request for something, usually made in writing.", "đơn xin", "noun", "She sent her job application yesterday."),
        ("responsible", "Having a duty to deal with or take care of something.", "chịu trách nhiệm", "adjective", "She is responsible for training new staff."),
        ("independent", "Able to act or live without help from others.", "tự lập, không phụ thuộc", "adjective", "University taught him to be more independent."),
        ("likely", "Expected to happen or probably true.", "có khả năng", "adjective", "Prices are likely to rise next year."),
        ("realise", "To become aware of or understand a fact.", "nhận ra", "verb", "I realised that I had taken the wrong bus."),
        ("recommend", "To say that someone or something is good or suitable.", "đề xuất, giới thiệu", "verb", "I recommend visiting the museum early."),
        ("avoid", "To stay away from someone or something.", "tránh", "verb", "Try to avoid the city centre during rush hour."),
        ("compare", "To examine how two or more things are similar or different.", "so sánh", "verb", "We compared the prices before buying."),
        ("consider", "To think carefully about something.", "cân nhắc", "verb", "You should consider all the options."),
        ("afford", "To have enough money to buy something.", "đủ khả năng chi trả", "verb", "We cannot afford a new car."),
        ("develop", "To grow or cause something to become more advanced.", "phát triển", "verb", "The course helped her develop her skills."),
        ("manage", "To succeed in doing something difficult.", "xoay xở, làm được", "verb", "We managed to finish the work on time."),
        ("announce", "To make something known publicly or officially.", "công bố", "verb", "They announced the results yesterday."),
    ],
    "B2": [
        ("significant", "Important or large enough to have a noticeable effect.", "đáng kể, quan trọng", "adjective", "The policy led to a significant reduction in waste."),
        ("beneficial", "Helpful, useful, or having a good effect.", "có ích, có lợi", "adjective", "Regular exercise is beneficial to your health."),
        ("acknowledge", "To accept or admit that something is true.", "thừa nhận", "verb", "The report acknowledges several weaknesses in the plan."),
        ("assumption", "Something accepted as true without definite proof.", "giả định", "noun", "Their forecast was based on a false assumption."),
        ("consequence", "A result of a particular action or situation.", "hệ quả", "noun", "One consequence of the delay was higher costs."),
        ("controversy", "Public disagreement about an important issue.", "cuộc tranh cãi", "noun", "The proposal caused considerable controversy."),
        ("criterion", "A standard used to judge or decide something.", "tiêu chí", "noun", "Cost is only one criterion for choosing a supplier."),
        ("decline", "A gradual reduction in amount, quality, or importance.", "sự suy giảm", "noun", "The region experienced a decline in tourism."),
        ("emphasis", "Special importance or attention given to something.", "sự nhấn mạnh", "noun", "The course places emphasis on practical communication."),
        ("evidence", "Facts or information that support a conclusion.", "bằng chứng", "noun", "There is strong evidence that exercise improves sleep."),
        ("factor", "A fact or condition that influences a result.", "yếu tố", "noun", "Price was an important factor in our decision."),
        ("impact", "A strong effect that something has on a situation.", "tác động", "noun", "Remote work has had an impact on city centres."),
        ("crucial", "Extremely important or necessary.", "rất quan trọng, thiết yếu", "adjective", "Accurate data is crucial to the project's success."),
        ("perspective", "A particular way of considering something.", "góc nhìn", "noun", "The documentary presents the conflict from both perspectives."),
        ("policy", "An agreed set of ideas or rules used by an organisation.", "chính sách", "noun", "The company introduced a flexible working policy."),
        ("principle", "A basic belief or rule that guides behaviour.", "nguyên tắc", "noun", "Fairness is a central principle of the programme."),
        ("relevant", "Directly connected with the subject being considered.", "có liên quan", "adjective", "Please include only relevant information in your answer."),
        ("adequate", "Enough or satisfactory for a particular purpose.", "đủ, phù hợp", "adjective", "The room provides adequate space for the meeting."),
        ("substantial", "Large in amount, value, or importance.", "đáng kể, lớn", "adjective", "The project requires a substantial investment."),
        ("tendency", "A way of behaving that is likely to continue.", "xu hướng", "noun", "He has a tendency to avoid difficult conversations."),
        ("assess", "To judge the quality, importance, or value of something.", "đánh giá", "verb", "The panel will assess each application carefully."),
        ("clarify", "To make a statement or situation easier to understand.", "làm rõ", "verb", "Could you clarify what the final paragraph means?"),
        ("contribute", "To give something that helps achieve a result.", "đóng góp", "verb", "Everyone contributed ideas to the discussion."),
        ("demonstrate", "To show or make something clear.", "chứng minh, minh họa", "verb", "The experiment demonstrates the effect of heat on metal."),
        ("distinguish", "To recognise the difference between two things.", "phân biệt", "verb", "It is difficult to distinguish fact from opinion."),
        ("establish", "To start a company or organisation that will continue for a long time.", "thành lập, thiết lập", "verb", "The university established a new research centre."),
        ("maintain", "To keep something in good condition or at the same level.", "duy trì", "verb", "It is hard to maintain motivation during a long project."),
        ("negotiate", "To discuss something formally in order to reach agreement.", "đàm phán", "verb", "The two sides negotiated a new contract."),
        ("overcome", "To succeed in dealing with a problem or difficulty.", "vượt qua", "verb", "She overcame her fear of public speaking."),
        ("justify", "To give a good reason for something.", "biện minh, chứng minh là hợp lý", "verb", "You must justify your conclusion with evidence."),
    ],
    "C1": [
        ("comprehensive", "Including all or nearly all relevant aspects.", "toàn diện", "adjective", "The review provides a comprehensive account of the evidence."),
        ("articulate", "Able to express ideas clearly and effectively.", "có khả năng diễn đạt rõ ràng", "adjective", "She is an articulate advocate for educational reform."),
        ("corruption", "Dishonest or illegal behaviour, especially by people in positions of power.", "sự tham nhũng", "noun", "The investigation uncovered widespread corruption."),
        ("counterpart", "A person or thing with the same purpose as another in a different place or organisation.", "người hoặc vật tương ứng", "noun", "The minister met her European counterparts."),
        ("constraint", "A limit or restriction on what can be done.", "sự hạn chế, ràng buộc", "noun", "Limited funding is a major constraint on the research."),
        ("comparable", "Similar in size, amount, or quality to something else.", "có thể so sánh", "adjective", "The two studies produced comparable results."),
        ("implication", "A possible effect that an action or decision may have in the future.", "hệ quả, tác động có thể có", "noun", "The discovery has important implications for public health."),
        ("innovation", "A new idea, method, or product.", "sáng kiến, sự đổi mới", "noun", "The new battery design is a major innovation."),
        ("insight", "A clear and deep understanding of a complex situation.", "sự thấu hiểu", "noun", "The interviews offer insight into consumer behaviour."),
        ("integrity", "The quality of being honest and guided by strong principles.", "sự chính trực", "noun", "Scientific integrity requires researchers to report all results."),
        ("phenomenon", "A fact or event that can be observed and studied.", "hiện tượng", "noun", "Urban migration is a complex social phenomenon."),
        ("prevalence", "The state of being common or widespread.", "mức độ phổ biến", "noun", "The survey measured the prevalence of online harassment."),
        ("rationale", "The reasons or principles that explain a decision.", "cơ sở lý luận", "noun", "The minister explained the rationale behind the reform."),
        ("resilience", "The ability to recover from difficulty or change.", "khả năng phục hồi", "noun", "The community showed remarkable resilience after the storm."),
        ("scrutiny", "Careful and detailed examination.", "sự xem xét kỹ lưỡng", "noun", "The figures came under intense public scrutiny."),
        ("synthesis", "The combination of ideas into a connected whole.", "sự tổng hợp", "noun", "Her conclusion is a synthesis of several competing theories."),
        ("viable", "Capable of working successfully in practice.", "khả thi", "adjective", "Solar power is now a viable option for the village."),
        ("compelling", "So strong that it makes you believe or accept it.", "có sức thuyết phục", "adjective", "The author presents a compelling case for reform."),
        ("allegation", "A statement made without proof that someone has done something wrong or illegal.", "cáo buộc chưa được chứng minh", "noun", "The company denied allegations of illegal payments."),
        ("nuanced", "Showing subtle differences or careful distinctions.", "tinh tế, nhiều sắc thái", "adjective", "The article offers a nuanced analysis of inequality."),
        ("profound", "Very great or intense.", "sâu sắc", "adjective", "The invention had a profound effect on modern life."),
        ("reluctant", "Not willing to do something and therefore slow to do it.", "miễn cưỡng, không sẵn lòng", "adjective", "She was reluctant to discuss the problem in public."),
        ("facilitate", "To make an action or process easier.", "tạo điều kiện", "verb", "Digital tools can facilitate international collaboration."),
        ("formulate", "To develop a plan or idea carefully and systematically.", "xây dựng, hình thành", "verb", "The team formulated a strategy based on the findings."),
        ("enforce", "To make people obey a law or rule.", "thi hành, buộc tuân thủ", "verb", "The authorities must enforce the new safety regulations."),
        ("mitigate", "To make something harmful less severe.", "giảm nhẹ", "verb", "New drainage systems could mitigate the risk of flooding."),
        ("reinforce", "To provide more proof or support for an idea or opinion.", "củng cố, làm tăng sức thuyết phục", "verb", "The latest results reinforce our earlier conclusion."),
        ("eligible", "Having the necessary qualities or satisfying the necessary conditions.", "đủ điều kiện, có đủ tư cách", "adjective", "Only residents over 18 are eligible to vote."),
        ("undermine", "To gradually weaken confidence, authority, or effectiveness.", "làm suy yếu", "verb", "Inconsistent rules can undermine public trust."),
        ("advocate", "To publicly support a policy or course of action.", "ủng hộ, vận động cho", "verb", "Many experts advocate investing in preventive care."),
    ],
    "C2": [
        ("ubiquitous", "Present or found almost everywhere.", "có mặt khắp nơi", "adjective", "Digital payment systems have become ubiquitous in large cities."),
        ("serendipity", "The accidental discovery of something valuable or interesting.", "sự tình cờ may mắn", "noun", "The breakthrough was partly the result of serendipity."),
        ("acquiesce", "To accept something reluctantly but without protest.", "miễn cưỡng chấp thuận", "verb", "The board eventually acquiesced to the revised proposal."),
        ("anachronism", "A person, thing, or idea that exists out of its time in history.", "người, vật hoặc ý tưởng lỗi thời, sai niên đại", "noun", "The manual filing system is an anachronism in a digital office."),
        ("apocryphal", "Widely repeated but probably not true.", "không xác thực", "adjective", "The apocryphal story has been attributed to several scientists."),
        ("capricious", "Changing suddenly and unpredictably.", "thất thường", "adjective", "Investors struggled to anticipate the capricious market."),
        ("conundrum", "A difficult and confusing problem.", "vấn đề nan giải", "noun", "Balancing privacy with security remains a conundrum."),
        ("dichotomy", "A division between two sharply contrasting things.", "sự phân đôi đối lập", "noun", "The essay challenges the dichotomy between nature and culture."),
        ("equivocal", "Unclear and able to be understood in two different ways.", "mơ hồ, nước đôi", "adjective", "His equivocal response failed to reassure the committee."),
        ("meticulous", "Very careful and with great attention to every detail.", "tỉ mỉ, kỹ lưỡng", "adjective", "The editor was meticulous about punctuation and tone."),
        ("incongruous", "Out of place or incompatible with the surroundings.", "không phù hợp", "adjective", "The modern sculpture looked incongruous in the medieval hall."),
        ("ineffable", "Causing so much emotion that it cannot be described in words.", "không thể diễn tả thành lời", "adjective", "The music evoked an ineffable sense of loss."),
        ("intransigent", "Unwilling to change an opinion or reach agreement.", "không khoan nhượng", "adjective", "Both parties remained intransigent throughout the talks."),
        ("laconic", "Using very few words.", "kiệm lời", "adjective", "Her laconic reply revealed little about her intentions."),
        ("magnanimous", "Generous and forgiving, especially towards a rival.", "cao thượng, rộng lượng", "adjective", "He was magnanimous in victory and praised his opponent."),
        ("obfuscate", "To make something less clear and harder to understand, especially intentionally.", "làm mơ hồ, khiến khó hiểu", "verb", "Technical jargon can obfuscate an otherwise simple argument."),
        ("parsimonious", "Small in size or amount.", "ít ỏi, eo hẹp", "adjective", "A parsimonious budget left no room for staff training."),
        ("pernicious", "Having a very harmful effect or influence.", "rất có hại, gây ảnh hưởng nguy hại", "adjective", "Misinformation can have a pernicious influence on public debate."),
        ("quintessential", "Representing the most typical example of a quality or class.", "điển hình nhất", "adjective", "The novel is a quintessential example of social satire."),
        ("recalcitrant", "Stubbornly unwilling to obey rules or authority.", "ngoan cố, bất phục tùng", "adjective", "Officials struggled to enforce the rule among recalcitrant firms."),
        ("sagacious", "Showing excellent judgement and practical wisdom.", "khôn ngoan, sáng suốt", "adjective", "Her sagacious advice prevented an expensive mistake."),
        ("sycophant", "A person who praises powerful or rich people insincerely to gain an advantage.", "kẻ xu nịnh", "noun", "The ruler surrounded himself with sycophants who never disagreed."),
        ("tenuous", "Very weak, slight, or uncertain.", "mong manh, thiếu cơ sở", "adjective", "The alleged connection between the events is tenuous."),
        ("vitriolic", "Full of violent hate and anger.", "đầy hằn học, cay độc", "adjective", "The debate descended into vitriolic personal attacks."),
        ("zeitgeist", "The defining ideas and mood of a particular period.", "tinh thần thời đại", "noun", "The film captured the rebellious zeitgeist of the decade."),
        ("circumspect", "Careful to consider risks before acting or speaking.", "thận trọng", "adjective", "Diplomats were circumspect in their public comments."),
        ("deleterious", "Causing harm or damage.", "có hại", "adjective", "Chronic sleep loss has deleterious effects on concentration."),
        ("elucidate", "To explain something complex and make it clear.", "làm sáng tỏ", "verb", "The diagram helps elucidate the relationship between the variables."),
        ("idiosyncratic", "Having unusual features characteristic of one person or thing.", "mang tính đặc thù, khác thường", "adjective", "The director is known for her idiosyncratic visual style."),
        ("perspicacious", "Quick to notice, understand, or judge things accurately.", "nhạy bén, sáng suốt", "adjective", "His perspicacious analysis anticipated the political shift."),
    ],
}

_PHONETICS = {
    "family": "/ˈfæm.əl.i/", "happy": "/ˈhæp.i/", "journey": "/ˈdʒɜː.ni/",
    "polite": "/pəˈlaɪt/", "opportunity": "/ˌɒp.əˈtʃuː.nə.ti/",
    "convenient": "/kənˈviː.ni.ənt/", "significant": "/sɪɡˈnɪf.ɪ.kənt/",
    "beneficial": "/ˌben.ɪˈfɪʃ.əl/", "comprehensive": "/ˌkɒm.prɪˈhen.sɪv/",
    "articulate": "/ɑːˈtɪk.jə.lət/", "ubiquitous": "/juːˈbɪk.wɪ.təs/",
    "serendipity": "/ˌser.ənˈdɪp.ə.ti/",
}

CEFR_VOCABULARY = [
    {"word": word, "definition": definition, "phonetic": _PHONETICS.get(word, ""),
     "meaning": meaning, "level": level, "part_of_speech": part_of_speech,
     "example": example, "provenance_type": PROVENANCE_AI_GENERATED,
     "source_reference": None, "qa_status": QA_STATUS_NEEDS_REVIEW}
    for level in CEFR_LEVELS
    for word, definition, meaning, part_of_speech, example in _ROWS[level]
]


def validate_cefr_vocabulary(items: list[dict] | None = None) -> None:
    """Raise ``ValueError`` for structural errors or unsupported QA claims.

    Semantic correctness (meaning, part of speech, example, and CEFR level) must
    still be checked against a cited source before an item can be ``VERIFIED``.
    """
    vocabulary = CEFR_VOCABULARY if items is None else items
    counts = Counter(item.get("level") for item in vocabulary)
    expected_counts = Counter({level: 30 for level in CEFR_LEVELS})
    if counts != expected_counts:
        raise ValueError(f"Expected exactly 30 words per CEFR level: {dict(counts)}")
    words = [str(item.get("word", "")).strip().casefold() for item in vocabulary]
    duplicates = [word for word, count in Counter(words).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate vocabulary words: {duplicates}")
    required = {
        "word",
        "definition",
        "meaning",
        "level",
        "part_of_speech",
        "example",
        "provenance_type",
        "qa_status",
    }
    for index, item in enumerate(vocabulary):
        empty = [field for field in required if not str(item.get(field, "")).strip()]
        if empty:
            raise ValueError(f"Vocabulary row {index} has empty fields: {empty}")
        if not _WORD_PATTERN.fullmatch(item["word"]):
            raise ValueError(f"Invalid headword format: {item['word']}")
        if item["part_of_speech"] not in PARTS_OF_SPEECH:
            raise ValueError(f"Unsupported part of speech for {item['word']}: {item['part_of_speech']}")
        if len(item["definition"].split()) < 3:
            raise ValueError(f"Definition is too short: {item['word']}")
        if len(item["example"].split()) < 4:
            raise ValueError(f"Example is too short: {item['word']}")
        if not item["definition"].endswith((".", "!", "?")):
            raise ValueError(f"Definition is not a sentence: {item['word']}")
        if not item["example"].endswith((".", "!", "?")):
            raise ValueError(f"Example is not a sentence: {item['word']}")
        text_fields = (item["word"], item["definition"], item["meaning"], item["example"])
        if any(marker in text for marker in _MOJIBAKE_MARKERS for text in text_fields):
            raise ValueError(f"Possible mojibake in vocabulary item: {item['word']}")

        provenance_type = item["provenance_type"]
        qa_status = item["qa_status"]
        source_reference = item.get("source_reference")
        if provenance_type not in _ALLOWED_PROVENANCE_TYPES:
            raise ValueError(f"Unsupported provenance for {item['word']}: {provenance_type}")
        if qa_status not in _ALLOWED_QA_STATUSES:
            raise ValueError(f"Unsupported QA status for {item['word']}: {qa_status}")
        if provenance_type == PROVENANCE_SOURCE_VERIFIED and not source_reference:
            raise ValueError(f"Source-verified item lacks a reference: {item['word']}")
        if qa_status == QA_STATUS_VERIFIED and (
            provenance_type != PROVENANCE_SOURCE_VERIFIED or not source_reference
        ):
            raise ValueError(f"Verified item lacks source evidence: {item['word']}")
        if provenance_type == PROVENANCE_AI_GENERATED and qa_status != QA_STATUS_NEEDS_REVIEW:
            raise ValueError(f"AI-generated item must remain NEEDS_REVIEW: {item['word']}")


validate_cefr_vocabulary()
