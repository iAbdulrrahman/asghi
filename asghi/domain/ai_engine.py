"""AIEngine class.
Matches class-diagram.puml, note on AIEngine, and Requirements 3.1, 3.2, 3.3, 7.2.
"""
from __future__ import annotations
from typing import List, Optional
from uuid import UUID

from asghi.domain.enums import ContentStatus, Difficulty, Origin, QuestionType
from asghi.domain.passage import Passage
from asghi.domain.question import Question


class AIEngine:
    def __init__(self):
        pass

    def generatePassageText(self, passageId: UUID) -> str:
        """Generates Fusha passage text, setting status = PENDING_REVIEW and origin = AI."""
        target: Optional[Passage] = None
        for p in Passage._registry:
            if p.passageId == passageId:
                target = p
                break

        generated_text = (
            "كانَتِ اللُّغَةُ العَرَبِيَّةُ وَمَا زَالَتْ جِسْرًا حَضَارِيًّا يَرْبِطُ بَيْنَ الشُّعُوبِ. "
            "تَمَيَّزَتْ بِفَصَاحَتِهَا وَدِقَّةِ أَلْفَاظِهَا وَغَزَارَةِ مَعَانِيهَا. "
            "تُعَدُّ مُمَارَسَةُ الِاسْتِمَاعِ مِن أَهَمِّ وَسَائِلِ إِتْقَانِ الفُصْحَى."
        )

        if target:
            target.text = generated_text
            target.origin = Origin.AI
            target.changeStatus(ContentStatus.PENDING_REVIEW)

        return generated_text

    def generateQuestions(self, passageId: UUID, countOfQuestion: int) -> List[Question]:
        """Generates balanced questions across EASY, MEDIUM, and HARD, with status = PENDING_REVIEW and origin = AI."""
        target: Optional[Passage] = None
        for p in Passage._registry:
            if p.passageId == passageId:
                target = p
                break

        difficulties = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]
        generated: List[Question] = []

        sample_questions_data = [
            (
                "ما هي الميزة الأساسية للغة العربية المذكورة في النص؟",
                ["الفصاحة ودقة الألفاظ", "السرعة في النطق", "صعوبة القواعد", "قلة المفردات"],
                "الفصاحة ودقة الألفاظ",
                "يوضح النص أن اللغة العربية تميزت بفصاحتها ودقة ألفاظها وغزارة معانيها.",
                Difficulty.EASY,
            ),
            (
                "ما هو دور اللغة العربية كجسر حضاري وفق النص؟",
                ["ربط الشعوب ونقل المعرفة", "عزل الثقافات", "اقتصارها على التجارة فقط", "منع التبادل المعرفي"],
                "ربط الشعوب ونقل المعرفة",
                "يذكر النص صراحة أنها جسر حضاري يربط بين الشعوب.",
                Difficulty.MEDIUM,
            ),
            (
                "كيف تسهم ممارسة الاستماع في إتقان اللغة العربية الفصحى؟",
                ["تعد وسيلة جوهرية لترسيخ النطق الصحيح والفهم السليم", "تؤخر اكتساب المفردات", "تغني تماماً عن القراءة والكتابة", "تقتصر على اللهجات فقط"],
                "تعد وسيلة جوهرية لترسيخ النطق الصحيح والفهم السليم",
                "أكد النص أن ممارسة الاستماع من أهم وسائل إتقان الفصحى.",
                Difficulty.HARD,
            ),
        ]

        for i in range(countOfQuestion):
            q_template = sample_questions_data[i % len(sample_questions_data)]
            diff = difficulties[i % len(difficulties)]
            q = Question(
                promptText=q_template[0],
                answers=q_template[1],
                correctAnswer=q_template[2],
                explanation=q_template[3],
                passageReference=f"فقرة { (i % 3) + 1 }",
                difficulty=diff,
                type=QuestionType.MCQ,
                passageId=passageId,
                authorId=None,  # authorId == null <=> origin == AI
                status=ContentStatus.PENDING_REVIEW,
                origin=Origin.AI,
            )
            if target:
                target.addQuestion(q)
            generated.append(q)

        return generated
