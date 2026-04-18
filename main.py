from fastapi import (
    FastAPI,
    HTTPException,
    Header,
    UploadFile,
    File,
    Form
)

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

import json
import os
import uvicorn


load_dotenv()

app = FastAPI()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

KNOWLEDGE_FILE = "knowledge.json"
LESSONS_FILE = "lessons.json"
EXPERTS_FILE = "experts.json"
USERS_FILE = "users.json"
IDEAS_FILE = "ideas.json"

# Ensure the file exists so load_json doesn't fail
if not os.path.exists(IDEAS_FILE):
    with open(IDEAS_FILE, "w") as f:
        json.dump([], f)

class IdeaEntry(BaseModel):
    title: str
    description: str
    department: str
    user: str
    status: str = "draft"  # Default status
    comment: str = ""      # Manager/Admin feedback
    
os.makedirs("uploads", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
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

def check_permission(role: str):
    if role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
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


@app.post("/signup")
def signup(user: dict):
    users = load_users()

    # check required fields
    if not user.get("name") or not user.get("email") or not user.get("password") or not user.get("role"):
        raise HTTPException(status_code=400, detail="All fields required")

    # check duplicate
    for u in users:
        if u["email"] == user["email"]:
            raise HTTPException(status_code=400, detail="User already exists")

    users.append(user)
    save_users(users)

    return {"message": "User created successfully"}


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/login")
def login(data: LoginRequest):
    users = load_users()

    for u in users:
        if u["email"] == data.email and u["password"] == data.password:
            return {
                "message": "Login successful",
                "user": {
                    "name": u["name"],
                    "email": u["email"],
                    "role": u["role"]
                }
            }

    raise HTTPException(status_code=401, detail="Invalid credentials")


# --- KNOWLEDGE ROUTES ---
@app.get("/knowledge")
def get_knowledge():
    return load_json(KNOWLEDGE_FILE)

@app.post("/knowledge/upload")
async def upload_knowledge(
    title: str = Form(...),
    content: str = Form(...),
    email: str = Form(...),
    file: UploadFile = File(None),
    role: str = Header(...)
):
    check_permission(role)

    data = load_json(KNOWLEDGE_FILE)

    filename = None

    if file:
        os.makedirs("uploads", exist_ok=True)

        file_location = f"uploads/{file.filename}"

        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())

        filename = file.filename

    data.append({
        "title": title,
        "content": content,
        "email": email,
        "file": filename
    })

    save_json(KNOWLEDGE_FILE, data)

    return {"message": "Knowledge uploaded successfully"}



@app.delete("/knowledge/{index}")
def delete_knowledge(index: int, role: str = Header(...)):
    check_permission(role)
    data = load_json(KNOWLEDGE_FILE)
    if 0 <= index < len(data):
        data.pop(index)
        save_json(KNOWLEDGE_FILE, data)
        return {"message": "Knowledge deleted successfully"}
    raise HTTPException(status_code=404, detail="Entry not found")

@app.put("/knowledge/{index}")
def update_knowledge(index: int, entry: KnowledgeEntry, role: str = Header(...)):
    check_permission(role)
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

# --- IDEAS ROUTES ---

@app.get("/ideas")
def get_ideas():
    return load_json(IDEAS_FILE)

@app.post("/ideas")
def add_idea(entry: IdeaEntry, role: str = Header(...)):
    # Optional: If you want to block employees from submitting, call check_permission(role)
    # If employees SHOULD be able to submit, leave as is.
    data = load_json(IDEAS_FILE)
    
    new_idea = entry.dict()
    # Force status to draft for new submissions regardless of what front-end sends
    new_idea["status"] = "draft" 
    
    data.append(new_idea)
    save_json(IDEAS_FILE, data)
    return {"message": "Idea submitted for review!"}

@app.put("/ideas/{index}")
def update_idea(index: int, entry: IdeaEntry, role: str = Header(...)):
    # If an employee tries to change the status, this raises 403 Forbidden
    if entry.status != "pending": # Example: only managers can move away from pending
        check_permission(role)
    
    data = load_json(IDEAS_FILE)
    if 0 <= index < len(data):
        data[index] = entry.dict()
        save_json(IDEAS_FILE, data)
        return {"message": "Update saved"}
    raise HTTPException(status_code=404, detail="Not found")

@app.delete("/ideas/{index}")
def delete_idea(index: int, role: str = Header(...)):
    check_permission(role)
    data = load_json(IDEAS_FILE)
    if 0 <= index < len(data):
        data.pop(index)
        save_json(IDEAS_FILE, data)
        return {"message": "Idea removed"}
    
    raise HTTPException(status_code=404, detail="Idea not found")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
