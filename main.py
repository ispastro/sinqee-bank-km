from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import json, os, uvicorn

load_dotenv()

app = FastAPI()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

KNOWLEDGE_FILE = "knowledge.json"
LESSONS_FILE = "lessons.json"
EXPERTS_FILE = "experts.json"


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


class Question(BaseModel):
    question: str

class KnowledgeEntry(BaseModel):
    title: str
    content: str

class LessonEntry(BaseModel):
    title: str
    lesson: str
    author: str

class ExpertEntry(BaseModel):
    name: str
    role: str
    expertise: str
    branch: str
    contact: str


@app.get("/")
def index():
    return FileResponse("index.html")

@app.get("/image.png")
def logo():
    return FileResponse("image.png")


@app.post("/ask")
def ask(body: Question):
    knowledge = load_json(KNOWLEDGE_FILE)
    lessons = load_json(LESSONS_FILE)
    experts = load_json(EXPERTS_FILE)

    knowledge_text = "\n\n".join([f"### {k['title']}\n{k['content']}" for k in knowledge])
    lessons_text = "\n\n".join([f"### {l['title']} (by {l['author']})\n{l['lesson']}" for l in lessons])
    experts_text = "\n\n".join([f"### {e['name']} — {e['role']} ({e['branch']})\nExpertise: {e['expertise']}\nContact: {e['contact']}" for e in experts])

    prompt = f"""You are a professional bank assistant for Siinqee Bank in Ethiopia.
Answer ONLY based on the knowledge provided below. If the answer is not found, say "I don't have information on that yet."
Be clear, helpful, and professional. If the question is about who to contact or who is an expert, refer to the Expert Directory.

--- KNOWLEDGE REPOSITORY ---
{knowledge_text}

--- LESSONS LEARNED ---
{lessons_text}

--- EXPERT DIRECTORY ---
{experts_text}

QUESTION: {body.question}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- KNOWLEDGE ROUTES ---
@app.get("/knowledge")
def get_knowledge():
    return load_json(KNOWLEDGE_FILE)

@app.post("/knowledge")
def add_knowledge(entry: KnowledgeEntry):
    data = load_json(KNOWLEDGE_FILE)
    data.append({"title": entry.title, "content": entry.content})
    save_json(KNOWLEDGE_FILE, data)
    return {"message": "Knowledge added successfully"}

@app.delete("/knowledge/{index}")
def delete_knowledge(index: int):
    data = load_json(KNOWLEDGE_FILE)
    if 0 <= index < len(data):
        data.pop(index)
        save_json(KNOWLEDGE_FILE, data)
        return {"message": "Knowledge deleted successfully"}
    raise HTTPException(status_code=404, detail="Entry not found")

@app.put("/knowledge/{index}")
def update_knowledge(index: int, entry: KnowledgeEntry):
    data = load_json(KNOWLEDGE_FILE)
    if 0 <= index < len(data):
        data[index] = {"title": entry.title, "content": entry.content}
        save_json(KNOWLEDGE_FILE, data)
        return {"message": "Knowledge updated successfully"}
    raise HTTPException(status_code=404, detail="Entry not found")


# --- LESSONS ROUTES ---
@app.get("/lessons")
def get_lessons():
    return load_json(LESSONS_FILE)

@app.post("/lessons")
def add_lesson(entry: LessonEntry):
    data = load_json(LESSONS_FILE)
    from datetime import date
    data.append({"title": entry.title, "lesson": entry.lesson, "author": entry.author, "date": str(date.today())})
    save_json(LESSONS_FILE, data)
    return {"message": "Lesson added successfully"}

@app.delete("/lessons/{index}")
def delete_lesson(index: int):
    data = load_json(LESSONS_FILE)
    if 0 <= index < len(data):
        data.pop(index)
        save_json(LESSONS_FILE, data)
        return {"message": "Lesson deleted successfully"}
    raise HTTPException(status_code=404, detail="Entry not found")

@app.put("/lessons/{index}")
def update_lesson(index: int, entry: LessonEntry):
    data = load_json(LESSONS_FILE)
    if 0 <= index < len(data):
        from datetime import date
        data[index] = {"title": entry.title, "lesson": entry.lesson, "author": entry.author, "date": data[index].get("date", str(date.today()))}
        save_json(LESSONS_FILE, data)
        return {"message": "Lesson updated successfully"}
    raise HTTPException(status_code=404, detail="Entry not found")


# --- EXPERTS ROUTES ---
@app.get("/experts")
def get_experts():
    return load_json(EXPERTS_FILE)

@app.post("/experts")
def add_expert(entry: ExpertEntry):
    data = load_json(EXPERTS_FILE)
    data.append(entry.dict())
    save_json(EXPERTS_FILE, data)
    return {"message": "Expert added successfully"}

@app.delete("/experts/{index}")
def delete_expert(index: int):
    data = load_json(EXPERTS_FILE)
    if 0 <= index < len(data):
        data.pop(index)
        save_json(EXPERTS_FILE, data)
        return {"message": "Expert deleted successfully"}
    raise HTTPException(status_code=404, detail="Entry not found")

@app.put("/experts/{index}")
def update_expert(index: int, entry: ExpertEntry):
    data = load_json(EXPERTS_FILE)
    if 0 <= index < len(data):
        data[index] = entry.dict()
        save_json(EXPERTS_FILE, data)
        return {"message": "Expert updated successfully"}
    raise HTTPException(status_code=404, detail="Entry not found")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
