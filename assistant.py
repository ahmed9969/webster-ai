import anthropic
import os
from vector_store import VectorStore

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

vector_store = VectorStore()

SYSTEM_PROMPT = """You are WebsterBot — a friendly, smart AI assistant for Webster University Tashkent students. Think of yourself as a helpful senior student who knows the university well and is always happy to chat.

YOUR PERSONALITY:
- Warm, friendly and conversational — like a real person, not a robot
- Use natural language, contractions, casual but respectful tone
- Show genuine interest in helping students
- Be encouraging and positive
- Keep responses concise unless detail is needed

HOW YOU BEHAVE:
- For greetings like "hi", "hello", "hey" — respond warmly and ask how you can help
- For casual chat — engage naturally like a friend would
- For Webster-specific questions — use the documents provided to give accurate answers
- For general questions about university life, studying, careers, academics — answer helpfully from your general knowledge even if it's not in the Webster documents
- For course recommendations, study tips, career advice — give genuine helpful advice
- NEVER say "I don't have information" for simple greetings or general questions
- Only refer to the admin office for very specific Webster administrative matters like exact fee amounts, specific dates, personal student records

WHAT YOU KNOW:
- You have access to Webster Tashkent documents about policies, courses and procedures
- You also have general knowledge about university life, studying, careers and academics
- Webster Tashkent offers these majors: BS Computer Science, BS Business Administration, BS Management Information Systems, BA International Relations, BA Economics, BA Psychology, BA Media Studies, LLB International Law, BS Chemistry, BS Nursing, Bachelor of Education Studies
- Webster is an American university with campuses worldwide including Tashkent, Uzbekistan
- Classes are taught in English
- Webster uses a standard American grading system (A, B, C, D, F)

LANGUAGE:
- Always respond in the same language the student uses
- English: casual and friendly
- Uzbek: warm and respectful  
- Russian: friendly and helpful

EXAMPLES OF GOOD RESPONSES:
- Student: "hello" → "Hey! 👋 Welcome to WebsterBot! I'm here to help you with anything Webster Tashkent related — courses, policies, academic advice, or just general questions. What's on your mind?"
- Student: "I'm stressed about exams" → "Exam stress is real! Here are some tips that actually work..." then give genuine advice
- Student: "what courses should i take" → Ask what their major is and what they enjoy, then give personalized advice
- Student: "how many credits to graduate" → Answer from the Webster documents

Remember: You are a helpful, knowledgeable friend — not a search engine that only works when documents match."""

def get_answer(question, language="en", history=[]):
    """Get answer to a student question"""
    
    webster_keywords = [
        "webster", "course", "credit", "graduate", "graduation", "major", "degree",
        "gpa", "grade", "grading", "policy", "register", "registration", "deadline",
        "fee", "tuition", "campus", "semester", "exam", "attendance", "transfer",
        "scholarship", "advisor", "department", "faculty", "requirement", "syllabus",
        "catalog", "schedule", "enroll", "enrollment", "academic", "program", "gcp"
    ]
    
    # Build full context from conversation history
    history_text = ""
    if history:
        for msg in history[-6:]:  # Last 6 messages for context
            role = "Student" if msg["role"] == "user" else "WebsterBot"
            history_text += f"{role}: {msg['content']}\n"
    
    # Combine history with current question for better search
    full_context_question = question
    if history:
        last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        full_context_question = last_user + " " + question
    
    question_lower = full_context_question.lower()
    needs_webster_docs = any(kw in question_lower for kw in webster_keywords)
    
    context = ""
    sources = []
    
    if needs_webster_docs:
        relevant_chunks = vector_store.search(full_context_question, top_k=5)
        if relevant_chunks:
            for chunk in relevant_chunks:
                context += f"\n---\nSource: {chunk['source']}\n{chunk['content']}\n"
                if chunk['source'] not in sources:
                    sources.append(chunk['source'])
    
    if context:
        user_prompt = f"""Previous conversation:
{history_text}
Student now asks: {question}

Relevant Webster documents:
{context}

Continue the conversation naturally, remembering what was discussed before.
Answer based on the documents and previous context.
Respond in the same language as the student."""
    else:
        user_prompt = f"""Previous conversation:
{history_text}
Student now asks: {question}

Continue the conversation naturally, remembering everything discussed before.
Be warm, friendly and helpful.
Respond in the same language as the student."""

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
    """Get course recommendations for a student"""
    
    relevant_chunks = vector_store.search(f"{major} courses requirements", top_k=8)
    
    context = ""
    for chunk in relevant_chunks:
        context += f"\n---\nSource: {chunk['source']}\n{chunk['content']}\n"
    
    prompt = f"""Based on the Webster University Tashkent course catalog, recommend courses for this student:

Major: {major}
Interests: {interests}
Completed Courses: {completed_courses if completed_courses else "None specified"}

COURSE CATALOG CONTEXT:
{context}

Please recommend:
1. Required courses they should take next
2. Elective courses that match their interests
3. Any important prerequisites to be aware of

Be specific with course names and explain why each is recommended."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
        
    except Exception as e:
        print(f"Claude API error: {e}")
        return "Sorry, I encountered an error generating recommendations."

def detect_language(text):
    """Simple language detection"""
    # Cyrillic characters suggest Russian or Uzbek
    cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    
    if cyrillic_count > len(text) * 0.3:
        # Check for Uzbek-specific words
        uzbek_words = ['salom', 'yordam', 'kurs', 'talaba', 'daraja', 'qanday', 'nima']
        text_lower = text.lower()
        if any(word in text_lower for word in uzbek_words):
            return "uz"
        return "ru"
    
    # Check for Latin Uzbek
    uzbek_latin = ["iltimos", "qanday", "nima", "salom", "rahmat"]
    text_lower = text.lower()
    if any(word in text_lower for word in uzbek_latin):
        return "uz"
    
    return "en"
