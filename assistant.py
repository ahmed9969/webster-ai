import anthropic
import os
import base64
from vector_store import VectorStore

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
vector_store = VectorStore()

SYSTEM_PROMPT = """You are WebsterBot, a friendly and knowledgeable academic advisor for Webster University Tashkent. You talk like a real human advisor — warm, conversational, and helpful. Not like a robot.

PERSONALITY:
- Friendly and approachable, like a helpful senior student or advisor
- Use natural language and contractions
- Show empathy and understanding
- Give practical, actionable advice
- Use "I" naturally, like "I'd recommend..." or "Honestly, I think..."
- Be encouraging and positive

HOW YOU BEHAVE:
- For greetings like "hi", "hello", "hey" — respond warmly and ask how you can help
- For casual chat — engage naturally like a friend would
- For Webster-specific questions — use the documents provided to give accurate answers
- For general questions about university life, studying, careers, academics — answer helpfully from your general knowledge
- NEVER say "I don't have information" for simple greetings or general questions
- Only refer to the admin office for very specific administrative matters like personal student records

CREDIT LOAD RULES (very important):
- First semester / new students: Maximum 13 credits
- Students with GPA 3.0 or above: Maximum 18 credits
- Students with GPA below 3.0: Maximum 16 credits
- Students on Academic Probation: Maximum 12 credits
- Summer term: Maximum 9 credits
- Overload (more than 18 credits) requires Dean approval and GPA 3.5+

WHEN ANALYZING UPLOADED DOCUMENTS:
- Read the document carefully and understand what it contains
- If it's a degree audit or transcript: identify completed courses, remaining requirements, GPA, credits earned
- Give specific, actionable advice based on what you see
- Recommend specific courses they should take next
- Point out any urgent requirements they might be missing
- Be encouraging and supportive

WHAT YOU KNOW:
- Webster Tashkent offers: BS Computer Science, BS Business Administration, BS Management Information Systems, BA International Relations, BA Economics, BA Psychology, BA Media Studies, LLB International Law, BS Chemistry, BS Nursing, Bachelor of Education Studies
- Webster is an American university with campuses worldwide including Tashkent, Uzbekistan
- Classes are taught in English
- Standard American grading system (A=4.0, B=3.0, C=2.0, D=1.0, F=0.0)
- Graduation requires minimum 128 credits and 2.0 GPA

LANGUAGE:
- Always respond in the same language the student uses
- English: casual and friendly
- Uzbek: warm and respectful
- Russian: friendly and helpful

Remember: You are a helpful, knowledgeable friend who works at Webster — not a search engine."""


def detect_language(text):
    cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    if cyrillic_count > len(text) * 0.3:
        uzbek_words = ['salom', 'yordam', 'kurs', 'talaba', 'daraja', 'qanday', 'nima']
        if any(word in text.lower() for word in uzbek_words):
            return "uz"
        return "ru"
    uzbek_latin = ["iltimos", "qanday", "nima", "salom", "rahmat"]
    if any(word in text.lower() for word in uzbek_latin):
        return "uz"
    return "en"


def get_context(question, history=[]):
    webster_keywords = [
        "webster", "course", "credit", "graduate", "graduation", "major", "degree",
        "gpa", "grade", "grading", "policy", "register", "registration", "deadline",
        "fee", "tuition", "campus", "semester", "exam", "attendance", "transfer",
        "scholarship", "advisor", "department", "faculty", "requirement", "syllabus",
        "catalog", "schedule", "enroll", "enrollment", "academic", "program", "gcp",
        "credit load", "maximum", "minimum", "first semester", "probation", "calendar",
        "spring", "fall", "summer", "drop", "withdraw", "dean", "overload"
    ]

    full_q = question
    if history:
        last = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        full_q = last + " " + question

    needs_docs = any(kw in full_q.lower() for kw in webster_keywords)
    context = ""
    sources = []

    if needs_docs:
        chunks = vector_store.search(full_q, top_k=5)
        for chunk in chunks:
            context += f"\n---\nSource: {chunk['source']}\n{chunk['content']}\n"
            if chunk['source'] not in sources:
                sources.append(chunk['source'])

    return context, sources


def extract_text_from_file(file_bytes, ext):
    """Extract text from uploaded files"""
    text = ""
    try:
        if ext == '.pdf':
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text()
        elif ext == '.docx':
            from docx import Document
            import io
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        elif ext == '.txt':
            text = file_bytes.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Text extraction error: {e}")
    return text


def analyze_document(file_bytes, ext, question, filename):
    """Analyze an uploaded document and give advice"""
    
    # Get Webster context for better advice
    webster_context, _ = get_context("course requirements graduation degree audit", [])
    
    is_image = ext in ['.png', '.jpg', '.jpeg']
    
    if is_image:
        # Send image directly to Claude
        b64_image = base64.standard_b64encode(file_bytes).decode('utf-8')
        media_type = "image/png" if ext == '.png' else "image/jpeg"
        
        prompt = f"""A Webster University Tashkent student has uploaded an image of their document.

Student's question: {question}

Relevant Webster University information:
{webster_context}

Please analyze this document image carefully. If it's a degree audit, transcript, or course plan:
1. Identify what courses they have completed
2. Identify what requirements they still need to fulfill
3. Recommend specific next steps and courses to take
4. Give advice on registration and course planning
5. Be encouraging and specific

If it's something else, help them with whatever they need based on the document."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )
        return message.content[0].text

    else:
        # Extract text from PDF/DOCX/TXT
        text = extract_text_from_file(file_bytes, ext)
        
        if not text.strip():
            return "I couldn't read the text from this file. Try uploading it as an image (screenshot) instead!"

        prompt = f"""A Webster University Tashkent student has uploaded their document: {filename}

Student's question: {question}

Document contents:
{text[:4000]}

Relevant Webster University information:
{webster_context}

Please analyze this document carefully. If it's a degree audit, transcript, or course plan:
1. Identify what courses they have completed and their grades
2. Identify what requirements they still need to fulfill
3. Calculate how many credits they still need
4. Recommend specific next courses to take based on what's remaining
5. Give practical advice on registration and course planning
6. Based on their GPA (if visible), tell them their maximum credit load
7. Be encouraging, specific and helpful

If it's something else, help them with whatever they need."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text


def get_answer(question, language="en", history=[]):
    context, sources = get_context(question, history)

    history_text = ""
    if history:
        for msg in history[-6:]:
            role = "Student" if msg["role"] == "user" else "WebsterBot"
            history_text += f"{role}: {msg['content']}\n"

    if context:
        user_prompt = f"""Previous conversation:
{history_text}
Student now asks: {question}

Relevant Webster documents:
{context}

Continue the conversation naturally. Respond in the same language as the student."""
    else:
        user_prompt = f"""Previous conversation:
{history_text}
Student now asks: {question}

Continue naturally. Be warm and friendly. Respond in the same language as the student."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return message.content[0].text, sources
    except Exception as e:
        print(f"Claude API error: {e}")
        return "Sorry, something went wrong. Please try again!", []


def get_course_recommendations(major, interests, completed_courses=""):
    context, _ = get_context(f"{major} courses requirements curriculum", [])

    prompt = f"""Based on the Webster University Tashkent course catalog, recommend courses for this student:

Major: {major}
Interests: {interests}
Completed Courses: {completed_courses if completed_courses else "None specified"}

Webster Document Context:
{context}

Please recommend:
1. Required courses they should take next
2. Elective courses that match their interests
3. Any important prerequisites to be aware of

Be specific with course names and explain why each is recommended. Be friendly and conversational."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Claude API error: {e}")
        return "Sorry, I encountered an error generating recommendations."