from flask import g, request

from service.api_definition import QUIZ_EDIT, USER, GET, PUBLIC, POST
from quiz.entities import quiz_question_entity, quiz_question_option_entity
from quiz import service
from service.db import db_session
from quiz.models import QuizQuestion, QuizQuestionOption, QuizAnswer
from service.entity import OrmSingeRelation
from sqlalchemy import func, exists, distinct
from membership.models import Member
from dataclasses import dataclass

service.entity_routes(
    path="/question",
    entity=quiz_question_entity,
    permission_list=QUIZ_EDIT,
    permission_read=QUIZ_EDIT,
    permission_create=QUIZ_EDIT,
    permission_update=QUIZ_EDIT,
    permission_delete=QUIZ_EDIT,
)

service.entity_routes(
    path="/question_options",
    entity=quiz_question_option_entity,
    permission_list=QUIZ_EDIT,
    permission_read=QUIZ_EDIT,
    permission_create=QUIZ_EDIT,
    permission_update=QUIZ_EDIT,
    permission_delete=QUIZ_EDIT,
)

service.related_entity_routes(
    path="/question/<int:related_entity_id>/options",
    entity=quiz_question_option_entity,
    relation=OrmSingeRelation('options', 'question_id'),
    permission_list=QUIZ_EDIT,
)


@service.route("/question/<int:question_id>/answer", method=POST, permission=USER)
def answer_question(question_id):
    data = request.json
    option_id = int(data["option_id"])

    option = db_session \
        .query(QuizQuestionOption) \
        .join(QuizQuestionOption.question) \
        .filter((QuizQuestion.id == question_id) & (QuizQuestionOption.id == option_id) & (QuizQuestionOption.deleted_at == None)) \
        .one_or_none()
    if option == None:
        return (400, f"Option id {option_id} is not an option for question id {question_id}")

    db_session.add(QuizAnswer(question_id=question_id, option_id=option_id, member_id=g.user_id, correct=option.correct))
    db_session.flush()

    question = db_session.query(QuizQuestion).get(question_id)
    json = quiz_question_entity.to_obj(question)
    json["options"] = []
    for option in question.options:
        option = quiz_question_option_entity.to_obj(option)
        json["options"].append(option)

    return json


@service.route("/next_question", method=GET, permission=USER)
def next_question(include_correct=False):
    # Find all questions that the user has correctly answered
    correct_questions = db_session.query(QuizQuestion.id) \
        .join(QuizQuestion.answers) \
        .filter(QuizAnswer.member_id == g.user_id) \
        .filter((QuizAnswer.correct) & (QuizAnswer.deleted_at == None))

    # Find questions which the user has not yet answered correctly
    q = db_session.query(QuizQuestion) \
        .filter(QuizQuestion.id.notin_(correct_questions)) \
        .filter(QuizQuestion.deleted_at == None) \
        .order_by(func.random())

    # Pick the first one
    question = q.first()

    if question is None:
        return None

    json = quiz_question_entity.to_obj(question)
    json["options"] = []
    for option in question.options:
        option = quiz_question_option_entity.to_obj(option)
        del option["correct"]
        del option["answer_description"]
        json["options"].append(option)

    del json["answer_description"]

    return json


@service.route("/unfinished", method=GET, permission=PUBLIC)
def quiz_member_answer_stats_route():
    return quiz_member_answer_stats()

@dataclass(frozen=True)
class QuizMemberStat:
    member_id: int
    remaining_questions: int
    correctly_answered_questions: int

def quiz_member_answer_stats():
    ''' Returns all members which haven't completed the quiz'''

    # Calculates how many questions each member has answered correctly
    # Includes an entry for all members, even if it is zero
    correctly_answered_questions = db_session.query(Member.member_id, func.count(distinct(QuizAnswer.option_id)).label("count")) \
        .join(QuizAnswer, Member.member_id==QuizAnswer.member_id, isouter=True) \
        .join(QuizAnswer.question, isouter=True) \
        .filter((QuizAnswer.id == None) | ((QuizAnswer.correct) & (QuizAnswer.deleted_at == None) & (QuizQuestion.deleted_at == None))) \
        .group_by(Member.member_id) \
        .subquery()

    question_count = db_session.query(QuizQuestion).filter(QuizQuestion.deleted_at == None).count()

    members = db_session.query(Member.member_id, correctly_answered_questions.c.count) \
        .join(correctly_answered_questions, (correctly_answered_questions.c.member_id==Member.member_id)) \
        .filter(Member.deleted_at == None)

    return [
        QuizMemberStat(
            member_id=member[0],
            remaining_questions=question_count - member[1],
            correctly_answered_questions=member[1],
         ) for member in members.all()
    ]

@service.route("/statistics", method=GET, permission=PUBLIC)
def quiz_statistics():
    # How many members have answered the quiz that should have

    # Correct percentage per question
    # Average correct percentage per member

    # Converts a list of rows of IDs and values to a map from id to value
    def mapify(rows):
        return {r[0]: r[1] for r in rows}

    questions = db_session.query(QuizQuestion).filter(QuizQuestion.deleted_at == None, QuizQuestionOption.deleted_at == None).join(QuizQuestion.options).all()

    # Note: counts each member at most once per question. So multiple mistakes on the same question are not counted
    incorrect_answers_by_question = mapify(db_session.query(QuizAnswer.question_id, func.count(distinct(QuizAnswer.member_id))).filter(QuizAnswer.correct == False).group_by(QuizAnswer.question_id).all())
    answers_by_question = mapify(db_session.query(QuizAnswer.question_id, func.count(distinct(QuizAnswer.member_id))).filter(QuizAnswer.deleted_at == None).group_by(QuizAnswer.question_id).all())

    first_answer_by_member = db_session.query(QuizAnswer.member_id, QuizAnswer.question_id, func.min(QuizAnswer.id).label("id")).filter(QuizAnswer.deleted_at == None).group_by(QuizAnswer.member_id, QuizAnswer.question_id).subquery()

    answers_by_option = mapify(
        db_session.query(QuizAnswer.option_id, func.count(distinct(QuizAnswer.member_id))) \
        .join(first_answer_by_member, (QuizAnswer.question_id == first_answer_by_member.c.question_id) & (QuizAnswer.member_id == first_answer_by_member.c.member_id)) \
        .filter(QuizAnswer.id == first_answer_by_member.c.id) \
        .group_by(QuizAnswer.option_id) \
        .all()
    )

    seconds_to_answer_quiz = list(db_session.execute("select TIME_TO_SEC(TIMEDIFF(max(created_at), min(created_at))) as t from quiz_answers group by member_id order by t asc;"))
    median_seconds_to_answer_quiz = seconds_to_answer_quiz[len(seconds_to_answer_quiz)//2][0] if len(seconds_to_answer_quiz) > 0 else 0


    return {
        "median_seconds_to_answer_quiz": median_seconds_to_answer_quiz,
        # Maximum number members that have answered any question.
        # This ensures we also account for questions added later (which may not have as many answers)
        # We iterate through the questions list to ensure we dont count deleted questions
        "answered_quiz_member_count": max([answers_by_question.get(question.id, 0) for question in questions]),
        "questions": [
            {
                "question": quiz_question_entity.to_obj(question),
                "options": [
                    {
                        "answer_count": answers_by_option.get(option.id, 0),
                        "option": quiz_question_option_entity.to_obj(option)
                    } for option in question.options
                ],
                # Number of unique members that have answered this question
                "member_answer_count": answers_by_question.get(question.id, 0),
                "incorrect_answer_fraction": sum(answers_by_option.get(option.id, 0) for option in question.options if not option.correct) / answers_by_question.get(question.id, 1),
            }
            for question in questions
        ]
    }