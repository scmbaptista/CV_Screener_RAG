# CV Screener RAG — Video Presentation Materials
## Leadtech Full-Stack AI Engineer Technical Task

---

# PART 1: VIDEO SCRIPT

### Target Duration: 4 min 30 sec (leave margin for the 5 min limit)

---

## 🎬 BEFORE YOU START

- **Tool:** Loom (loom.com), OBS, or QuickTime (Mac) / Xbox Game Bar (Win+G on Windows)
- **Resolution:** 1920x1080 or higher
- **Audio:** Clean microphone, silent environment
- **Preparation:** Have the backend running on `localhost:8000` and the 30 generated CVs ready

---

## 📝 DETAILED SCRIPT

---

### INTRODUCTION (0:00 – 0:30)

**[Show: Browser screen with the CV Screener RAG open]**

**Say:**
> "Hello, I'm Sandra Baptista. This is my prototype for the Leadtech technical challenge: a CV Screener with RAG — Retrieval-Augmented Generation. The goal is simple: allow a recruiter to ask questions in natural language about a CV database and receive grounded answers, with source indication. I'll show you in 4 minutes how this works, from start to finish."

**[Transition: Switch to terminal]**

---

### PART 1: THE PROCESS — Data Generation (0:30 – 1:30)

**[Show: Terminal with the generation command running]**

**Say:**
> "First, data generation. Instead of scraping real CVs — which would raise privacy issues — I chose to generate 30 synthetic CVs, completely fictional but realistic."

**[Show: Run in terminal]**
```bash
python3 generate_cvs.py
```

**[Show: The terminal output creating the 30 CVs]**

**Say:**
> "Each CV has a programmatically generated photo — avatars with initials, not real people's photos — contact info, professional summary, work experience, education, skills, and languages. I used the Faker library with a fixed seed, making the dataset 100% reproducible."

**[Show: Open one or two generated PDFs to show the realistic look]**

**Say:**
> "Here's an example. Professional layout, well-defined sections, and a footer that clearly indicates it's synthetic. All in PDF, as requested."

**[Transition: Switch to IDE / VS Code]**

---

### PART 2: THE DEMO — Chat Interface (1:30 – 3:30)

**[Show: Browser on localhost:8000, the CV Screener welcome page]**

**Say:**
> "Now to the application. The backend is FastAPI, the frontend is vanilla HTML/CSS/JS — zero build step, maximum portability. On startup, the system extracts text from the PDFs, splits it into intelligent chunks, generates embeddings with the all-MiniLM-L6-v2 model, and stores everything in a persistent ChromaDB vector database."

**[Show: Look at the badges on top: "30 CVs" and "203 chunks"]**

**Say:**
> "We can see here that 30 CVs were indexed, resulting in 203 semantic chunks. Let's ask some questions."

**[Question 1 — Click the example button or type]**

**Ask:** *"Who has experience with Python?"*

**[Show: The answer loading, then the result with source badges]**

**Say:**
> "The question is converted into a semantic vector. The system searches for the 5 most relevant chunks in the vector database and, with the recovered context, generates an answer. Notice: every answer shows badges with the names of the candidates that were used as sources."

**[Question 2 — Type manually]**

**Ask:** *"Which candidate graduated from UPC?"*

**[Show: Answer with candidates who have UPC in their education]**

**Say:**
> "UPC — Universitat Politècnica de Catalunya. The system found the candidates who mention this university in the education section."

**[Question 3 — Safety test]**

**Ask:** *"diabetes"*

**[Show: Honest answer — "I don't have that information..."]**

**Say:**
> "Here's something important. If you ask something that doesn't exist in the CVs, the system doesn't make it up. I implemented a strict relevance filter based on keywords — if no word from the query appears in the retrieved chunks, the answer is honest: I don't have that information."

**[Question 4 — More complex question]**

**Ask:** *"Find candidates with AWS and Kubernetes skills"*

**[Show: Answer with candidates who have both skills]**

**Say:**
> "And it works with complex queries, combining multiple skills. Semantic search understands the context, it doesn't just do exact word matching."

**[Transition: Switch to IDE / VS Code with the code]**

---

### PART 3: TECHNICAL HIGHLIGHT (3:30 – 4:30)

**[Show: VS Code with the project open. Navigate to `backend/rag_engine.py`]**

**Say:**
> "The part I'm most proud of is the manual RAG pipeline, here in `rag_engine.py`. I chose not to use LangChain or LlamaIndex — frameworks that abstract too much. I wanted to demonstrate that I understand every step: chunking, embeddings, retrieval, and generation."

**[Scroll to the `_chunk_relevance_score` or `_filter_relevant_chunks` function]**

**Say:**
> "The most interesting challenge was avoiding false positives. The embedding model can return semantically close chunks that, in fact, don't contain the answer. I implemented this strict relevance filter: if no keyword from the query appears in the chunk, the score is zero. This prevents the system from hallucinating information."

**[Show: The contextualized chunking function — where it adds `[Name] [Section]` to the text]**

**Say:**
> "Another creative decision was contextualized chunking. Instead of blindly splitting the text, I preserve the CV section boundaries and prefix each chunk with the candidate's name and section. This drastically improves retrieval precision."

**[Quickly show `frontend/index.html` — single file, zero build]**

**Say:**
> "On the frontend, I went with vanilla HTML/CSS/JS in a single file. No React, no build step. The goal was a functional product, not a complex frontend architecture."

**[Transition: Back to the browser with the chat]**

---

### CONCLUSION (4:30 – 5:00)

**[Show: The chat running, maybe ask one last quick question]**

**Say:**
> "In summary: I generated 30 synthetic and privacy-safe CVs, built a complete RAG pipeline with local embeddings and a persistent vector database, and exposed everything through a simple and functional chat interface. The code is modular, documented, and ready to be extended. Thank you for the opportunity, and I look forward to your feedback."

**[Fade out or stop recording]**

---

## 💡 RECORDING TIPS

1. **Don't rush.** Speak slowly. The time is generous (4:30 target for a 5 min limit).
2. **Pause between sections.** Take a breath when switching screens.
3. **If you make a mistake, pause and restart.** Loom allows cutting afterwards.
4. **Keep the cursor visible.** The viewer needs to know where you're clicking.
5. **Test the questions beforehand.** Make sure the backend is responding well before recording.
6. **Show the terminal generating CVs in speed-up if it's too slow.** Loom has an option to accelerate clips.

---

## 🎥 TIME STRUCTURE (Summary)

| Time | Section | What to do |
|------|---------|------------|
| 0:00-0:30 | Introduction | Presentation + project goal |
| 0:30-1:30 | The Process | Terminal → `generate_cvs.py` → show PDFs |
| 1:30-3:30 | The Demo | Browser → 4 questions (Python, UPC, diabetes, AWS+K8s) |
| 3:30-4:30 | Technical Highlight | VS Code → `rag_engine.py` → filter + chunking |
| 4:30-5:00 | Conclusion | Summary + thank you |

---

---

# PART 2: AI VIDEO GENERATION PROMPT

Use this prompt with any AI video generation tool (HeyGen, Synthesia, D-ID, etc.)

---

## 🎬 CONTEXT

Create a professional presentation video of **4 minutes and 30 seconds** (max 5 min) for a technical recruitment challenge. The video must be presented by a digital avatar based on the photo I attached. The presentation is in **English** with a neutral/American accent. The tone is confident, professional but accessible, and enthusiastic without being exaggerated.

---

## AVATAR / PRESENTER

- **Appearance:** Use the attached photo as reference for the avatar. Must be realistic, professional, upright posture, friendly expression.
- **Clothing:** Business casual (shirt or blouse in a sober color).
- **Gesture:** Use natural hand gestures while speaking. Maintain eye contact with the camera. Smile lightly during the introduction and conclusion.
- **Position:** Avatar on the left or right side of the screen (split-screen layout), occupying about 25-30% of the frame. The rest of the space is for the product videos.

---

## VIDEO STRUCTURE AND SCRIPT

---

### INTRODUCTION (0:00 – 0:30)

**[Scene: Avatar in medium shot, clean background with a soft dark blue/gray gradient. Animated title: "CV Screener RAG — Leadtech Technical Task"]**

**Avatar says:**
> "Hello, I'm Sandra Baptista. This is my prototype for the Leadtech technical challenge: a CV Screener with RAG — Retrieval-Augmented Generation. The goal is simple: allow a recruiter to ask questions in natural language about a CV database and receive grounded answers, with source indication. I'll show you in 4 minutes how this works, from start to finish."

**[Transition: Smooth fade to split-screen]**

---

### PART 1: THE PROCESS — Data Generation (0:30 – 1:30)

**[Scene: Split-screen. Avatar on the left (20%). On the right, show the product video: terminal running `python3 generate_cvs.py` and then opening the generated PDFs.]**

**Avatar says:**
> "First, data generation. Instead of scraping real CVs — which would raise privacy issues — I chose to generate 30 synthetic CVs, completely fictional but realistic."

**[Product video: Show the terminal creating the 30 CVs, then open 1-2 PDFs to show the realistic layout]**

**Avatar says:**
> "Each CV has a programmatically generated photo — avatars with initials, not real people's photos — contact info, professional summary, work experience, education, skills, and languages. I used the Faker library with a fixed seed, making the dataset 100% reproducible."

**[Product video: Zoom on the generated PDF, showing sections and "synthetic" footer]**

**Avatar says:**
> "Here's an example. Professional layout, well-defined sections, and a footer that clearly indicates it's synthetic. All in PDF, as requested."

**[Transition: Lateral wipe to next scene]**

---

### PART 2: THE DEMO — Chat Interface (1:30 – 3:30)

**[Scene: Split-screen. Avatar on the left. On the right, show the product video: browser on `localhost:8000`, CV Screener homepage with "30 CVs" and "203 chunks" badges.]**

**Avatar says:**
> "Now to the application. The backend is FastAPI, the frontend is vanilla HTML/CSS/JS — zero build step, maximum portability. On startup, the system extracts text from the PDFs, splits it into intelligent chunks, generates embeddings with the all-MiniLM-L6-v2 model, and stores everything in a persistent ChromaDB vector database."

**[Product video: Show the top badges. Then demonstrate the first question]**

**Avatar says:**
> "We can see here that 30 CVs were indexed, resulting in 203 semantic chunks. Let's ask some questions."

**[Product video: Type "Who has experience with Python?" — show the loading response and source badges with candidate names]**

**Avatar says:**
> "The question is converted into a semantic vector. The system searches for the 5 most relevant chunks in the vector database and, with the recovered context, generates an answer. Notice: every answer shows badges with the names of the candidates that were used as sources."

**[Product video: Question 2 — "Which candidate graduated from UPC?" — show answer]**

**Avatar says:**
> "UPC — Universitat Politècnica de Catalunya. The system found the candidates who mention this university in the education section."

**[Product video: Question 3 — "diabetes" — show honest answer "I don't have that information..."]**

**Avatar says:**
> "Here's something important. If you ask something that doesn't exist in the CVs, the system doesn't make it up. I implemented a strict relevance filter based on keywords — if no word from the query appears in the retrieved chunks, the answer is honest: I don't have that information."

**[Product video: Question 4 — "Find candidates with AWS and Kubernetes skills" — show answer with multiple candidates]**

**Avatar says:**
> "And it works with complex queries, combining multiple skills. Semantic search understands the context, it doesn't just do exact word matching."

**[Transition: Smooth zoom out]**

---

### PART 3: TECHNICAL HIGHLIGHT (3:30 – 4:30)

**[Scene: Split-screen. Avatar on the left. On the right, show the product video: VS Code with `rag_engine.py` open. Scroll through the `_filter_relevant_chunks` function and then through the chunking function.]**

**Avatar says:**
> "The part I'm most proud of is the manual RAG pipeline, here in rag_engine.py. I chose not to use LangChain or LlamaIndex — frameworks that abstract too much. I wanted to demonstrate that I understand every step: chunking, embeddings, retrieval, and generation."

**[Product video: Highlight the code of the relevance function]**

**Avatar says:**
> "The most interesting challenge was avoiding false positives. The embedding model can return semantically close chunks that, in fact, don't contain the answer. I implemented this strict relevance filter: if no keyword from the query appears in the chunk, the score is zero. This prevents the system from hallucinating information."

**[Product video: Show the contextualized chunking function with `[Name] [Section]`]**

**Avatar says:**
> "Another creative decision was contextualized chunking. Instead of blindly splitting the text, I preserve the CV section boundaries and prefix each chunk with the candidate's name and section. This drastically improves retrieval precision."

**[Product video: Quickly show `frontend/index.html` — single file]**

**Avatar says:**
> "On the frontend, I went with vanilla HTML/CSS/JS in a single file. No React, no build step. The goal was a functional product, not a complex frontend architecture."

**[Transition: Fade to final scene]**

---

### CONCLUSION (4:30 – 5:00)

**[Scene: Avatar in medium shot. Background with the browser chat running smoothly in a loop (slight blur).]**

**Avatar says:**
> "In summary: I generated 30 synthetic and privacy-safe CVs, built a complete RAG pipeline with local embeddings and a persistent vector database, and exposed everything through a simple and functional chat interface. The code is modular, documented, and ready to be extended. Thank you for the opportunity, and I look forward to your feedback."

**[Animated final text: "Thank you! | github.com/... | linkedin.com/in/..."]"

**[Fade to black]**

---

## PRODUCTION INSTRUCTIONS

1. **Total duration:** Maximum 5 minutes. Calm pace, not rushed.
2. **Voice:** Female, clear, professional. Moderate speed (not rushed).
3. **Subtitles:** Enable English subtitles (CC) with a legible sans-serif font.
4. **Music:** Very soft instrumental background music (tech/corporate ambient), almost imperceptible during speech. Total silence during terminal demonstrations.
5. **Transitions:** Use only smooth fades and lateral wipes. No flashy effects.
6. **Product videos:** Sync the attached videos with the indicated timestamps. When the avatar mentions the terminal, show the terminal video. When mentioning the chat, show the browser video.
7. **Callouts:** Add subtle yellow arrows or highlights on the code when the avatar mentions specific functions (e.g., `_filter_relevant_chunks`).

---

## PROVIDED MATERIALS

- ✅ Avatar photo (attach)
- ✅ Product video: terminal + CV generation (attach — use in Part 1)
- ✅ Product video: browser + chat interface with the 4 questions (attach — use in Part 2)
- ✅ Product video: VS Code + rag_engine.py code (attach — use in Part 3)

---

## TOOL-SPECIFIC TIPS

| If you use... | What to do |
|---------------|------------|
| **HeyGen / D-ID** | Upload the photo as an avatar. Create a "script" with the text above and upload the product videos as "background scenes". |
| **Synthesia** | Use the photo to create a custom avatar. Add the videos as "media" in each slide. |
| **CapCut + AI** | Generate only the talking avatar with AI, then manually assemble with the product videos side by side. |
| **Loom (you presenting)** | Ignore the avatar. Use this script as a speaking guide, recording yourself with the product videos in split-screen. |

---

*Good recording! 🚀*
