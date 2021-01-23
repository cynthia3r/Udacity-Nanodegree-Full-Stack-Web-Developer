import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from db.models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        #self.database_path = "postgresql://{}/{}".format('localhost:5432', self.database_name)
        self.database_path = "postgresql://{}:{}@{}/{}".format('postgres', 'postgres', 'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        #sample question to be used for test
        self.new_question = {
            'question': 'Name the largest ocean in the world?',
            'answer': 'Pacific',
            'difficulty': 2,
            'category': '3',
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """

    """
    Test get endpoint for categories
    """
    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        self.assertTrue(len(data['categories']))

    """
    Test non-existent category
    """
    def test_404_get_request_non_existent_category(self):
        res = self.client().get('/categories/1000')
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    """
    Test question pagination
    """
    def test_get_paginated_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertTrue(len(data['categories']))

    """
    Test question pagination failure
    """
    def test_404_get_request_question_beyond_valid_page(self):
        res = self.client().get('/questions?page=500')
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

   
    """
    Test deletion of question
    """
    def test_delete_question(self):
        question = Question(question=self.new_question['question'], answer=self.new_question['answer'],
        difficulty=self.new_question['difficulty'], category=self.new_question['category'])

        question.insert()
        question_id = question.id

        res = self.client().delete(f'/questions/{question_id}')
        data = json.loads(res.data)

        question_result = Question.query.filter(Question.id == question_id).one_or_none()

        #check status and status message
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        self.assertEqual(data['deleted'], question_id)
        self.assertEqual(question_result, None)


    """
    Test non-existent question deletion
    """
    def test_422_delete_request_non_existent_question(self):
        res = self.client().delete('/questions/1599')
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')


    """
    Test new question creation
    """
    def test_create_new_question(self):
        #get questions before post request
        questions_before = Question.query.all()
        res = self.client().post('/questions', json=self.new_question)
        data = json.loads(res.data)

        #get questions after post request
        questions_after = Question.query.all()

        #check status and status message
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        #check if question was added after post request
        self.assertTrue(len(questions_after) - len(questions_before) == 1)

        #assert created question.id is not None
        self.assertIsNotNone(data['created'])

    """
    Test question creation failure
    """
    def test_422_create_new_question_failure(self):
        #get questions before post request
        questions_before = Question.query.all()
        res = self.client().post('/questions', json={})
        data = json.loads(res.data)

        #get questions after post request
        questions_after = Question.query.all()

        #check status and status message
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')

        #check if total questions before and after post request are equal
        self.assertTrue(len(questions_after) == len(questions_before))

    """
    Test search question
    """
    def test_search_question(self):
        res = self.client().post('/questions', json={'searchTerm': 'medicine'})
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        self.assertIsNotNone(data['questions'])
        self.assertIsNotNone(data['total_questions'])

    """
    Test search question failure
    """
    def test_404_search_question_failure(self):
        res = self.client().post('/questions', json={'searchTerm': 'invalidsearchterm'})
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')


    """
    Test get questions by categories
    """
    def test_get_questions_by_category(self):
        res = self.client().get('categories/3/questions')
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        
        self.assertTrue(len(data['questions']))
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['current_category'])

    """"
    Test get questions by categories failure
    """
    def test_404_get_questions_by_category(self):
        res = self.client().get('categories/3500/questions')
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    """
    Test random question selection for quiz
    """
    def test_random_question_selection_quiz(self):
        quiz_round_data = {'previous_questions': [], 
            'quiz_category': {
                'id': 3,
                'type': 'Geography',
            }
        }
        res = self.client().post('/quizzes', json=quiz_round_data)
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

    """
     Test random question selection failure for quiz
    """
    def test_422_random_question_selection_quiz_failure(self):
        res = self.client().post('/quizzes', json={})
        data = json.loads(res.data)

        #check status and status message
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()