from flask import Flask, render_template, request, jsonify
from assistant import get_answer, get_course_recommendations, detect_language
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '').strip()
    history = data.get('history', [])
    
    if not question:
        return jsonify({'error': 'Please enter a question'}), 400
    
    language = detect_language(question)
    answer, sources = get_answer(question, language, history)
    
    return jsonify({
        'answer': answer,
        'sources': sources,
        'language': language
    })

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    major = data.get('major', '').strip()
    interests = data.get('interests', '').strip()
    completed = data.get('completed', '').strip()
    
    if not major:
        return jsonify({'error': 'Please enter your major'}), 400
    
    recommendations = get_course_recommendations(major, interests, completed)
    
    return jsonify({'recommendations': recommendations})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
