import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from backend.db.models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

#Utility function for handling pagination
def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO COMPLETED: Set up CORS(Cross Origin Resource Sharing). Allow '*' for all origins. 
    Delete the sample route after completing the TODOs
  '''
  CORS(app, resources={"/": {"origin": "*"}})

  
  '''
  @TODO COMPLETED: CORS Headers. Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,PATCH,POST,DELETE,OPTIONS')
    return response


  '''
  @TODO COMPLETED: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
    categories = Category.query.order_by(Category.id).all()

    #abort if no categories found
    if len(categories) == 0:
      abort(404)

    # add all categories to dictionary so that the information can be send as part of response object
    categories_dict = {}
    for category in categories:
      categories_dict[category.id] = category.type

    #return the result in json format
    return jsonify({
      "success": True,
      "categories": categories_dict
    })

  '''
  @TODO COMPLETED: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories.
  '''
  @app.route('/questions')
  def get_questions():
    #query all questions and apply pagination
    selection = Question.query.order_by(Question.id).all()
    total_questions = len(selection)
    current_questions = paginate_questions(request, selection)

    #abort if no questions to be shown for the current paginated page
    if len(current_questions) == 0:
      abort(404)

    # add all categories to dictionary so that the information can be send as part of response object
    categories = Category.query.order_by(Category.id).all()
    categories_dict = {}
    for category in categories:
      categories_dict[category.id] = category.type
    
    #return the result in json format
    return jsonify({
      "success": True,
      "questions": current_questions,
      "total_questions": total_questions,
      "categories": categories_dict,
    })


  '''
  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''

  '''
  @TODO COMPLETED: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      #get question filtered by question_id
      question = Question.query.filter(Question.id == question_id).one_or_none()

      #abort if the query does not return any question
      if question is None:
        abort(404)

      #delete the question as returned by the filtered query
      question.delete()

      #prepare the information so that it can be send as part of response object
      selection = Question.query.order_by(Question.id).all()
      total_questions = len(selection)
      current_questions = paginate_questions(request, selection)

      #return the result in json format
      return jsonify({
        "success": True,
        "deleted": question_id,
        "questions": current_questions,
        "total_questions": total_questions,
      })
    
    except:
      abort(422)


  #Created a POST endpoint to handle following requests:
  #a.retrieve questions based on a search term
  #b.create new question based on information passed in request object
  @app.route('/questions', methods=['POST'])
  def create_question():
    #get the request body data in json format
    body = request.get_json()

    search_term = body.get('searchTerm', None)

    try:
      '''
      @TODO COMPLETED: 
      Create a POST endpoint to get questions based on a search term. 
      It should return any questions for whom the search term 
      is a substring of the question. 

      TEST: Search by any phrase. The questions list will update to include 
      only question that include that string within their question. 
      Try using the word "title" to start. 
      '''
      if search_term:
        #query the database table for search term
        selection = Question.query.filter(Question.question.ilike('%{}%'.format(search_term))).all()

         #abort if the search query does not return any result
        if(len(selection) == 0):
          abort(404)
        
        #apply pagination
        current_questions = paginate_questions(request, selection)

        #get the total number of questions
        total_questions = len(Question.query.all())
        #total_questions = len(current_questions)

        #return the result in json format
        return jsonify({
          "success": True,
          "questions": current_questions,
          "total_questions": total_questions,
        })
      else:
        '''
        @TODO COMPLETED: 
        Create an endpoint to POST a new question, 
        which will require the question and answer text, 
        category, and difficulty score.

        TEST: When you submit a question on the "Add" tab, 
        the form will clear and the question will appear at the end of the last page
        of the questions list in the "List" tab.  
        '''
        #get data from the body of the request object
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category =body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        #check if all fields contain data
        if((new_question is None) or (new_answer is None) or (new_category is None) or (new_difficulty is None)):
          abort(422)

        #create and insert new question in the database
        question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
        question.insert()

        #get all questions and apply pagination
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        #get the total number of questions
        total_questions = len(current_questions)

        #return the result in json format
        return jsonify({
          "success": True,
          "created": question.id,
          #"question_created": question.question,
          "questions": current_questions,
          "total_questions": total_questions,
        })

    except:
      abort(422)

  '''
  @TODO COMPLETED: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:id>/questions')
  def get_questions_by_category(id):
    #get category by category id
    category = Category.query.filter(Category.id == id).one_or_none()

    #abort if the category id does not exist
    if category is None:
      abort(404)

    #query all questions for the categoty id
    selection = Question.query.filter(Question.category == category.id).all()

    #get the total number of questions
    total_questions = len(Question.query.all())
    #total_questions = len(selection)
    
    #apply pagination
    current_questions = paginate_questions(request, selection)
    
    #return the result in json format
    return jsonify({
      "success": True,
      "questions": current_questions,
      "total_questions": total_questions,
      "current_category": category.type,
    })


  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''


  '''
  @TODO COMPLETED: 
  Create error handlers for all expected errors 
  including 400, 404, 422 and 500. 
  '''
  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False,
      "error": 400,
      "message": "bad request"
    }),400
  
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message": "resource not found"
    }),404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False,
      "error": 422,
      "message": "unprocessable"
    }),422

  @app.errorhandler(500)
  def internal_server_error(error):
    return jsonify({
      "success": False,
      "error": 500,
      "message": "internal server error"
    }),500
  
  return app

    