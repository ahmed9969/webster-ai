from flask import Flask, render_template, request, jsonify, Response
from assistant import get_answer, get_course_recommendations, detect_language, get_context, SYSTEM_PROMPT, analyze_document
import anthropic
import json
import os
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

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
    return jsonify({'answer': answer, 'sources': sources, 'language': language})

@app.route('/ask-stream', methods=['POST'])
def ask_stream():
    data = request.json
    question = data.get('question', '').strip()
    history = data.get('history', [])
    if not question:
        return jsonify({'error': 'Please enter a question'}), 400

    language = detect_language(question)
    context, sources = get_context(question, history)

    history_text = ""
    if history:
        for msg in history[-6:]:
            role = "Student" if msg["role"] == "user" else "WebsterBot"
            history_text += f"{role}: {msg['content']}\n"

    if context:
        user_prompt = f"Previous conversation:\n{history_text}\nStudent now asks: {question}\n\nRelevant Webster documents:\n{context}\n\nContinue the conversation naturally. Respond in the same language as the student."
    else:
        user_prompt = f"Previous conversation:\n{history_text}\nStudent now asks: {question}\n\nContinue naturally. Be warm and friendly. Respond in the same language as the student."

    def generate():
        try:
            client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps(text)}\n\n"
            src_str = ",".join(sources)
            yield f"data: [SOURCES:{src_str}]\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"Streaming error: {e}")
            yield f"data: {json.dumps('Sorry, something went wrong. Please try again.')}\n\n"
            yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/upload-document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    question = request.form.get('question', 'Please analyze this document and give me advice.')

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    allowed = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        return jsonify({'error': 'File type not supported. Please upload PDF, DOCX, TXT, or image files.'}), 400

    try:
        file_bytes = file.read()
        analysis = analyze_document(file_bytes, ext, question, file.filename)
        return jsonify({'answer': analysis, 'sources': [file.filename]})
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

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