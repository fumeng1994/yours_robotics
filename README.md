# Starter (optional)

This folder is here to save you boilerplate time. **Using it is entirely optional** — delete
it and start from scratch if you prefer, in any stack you like.

What's here:
- `summary.template.json` — the required `summary.json` shape (see `TASK_BRIEF.md`). Copy it
  to your repo root as `summary.json` and fill in the values your app computes.
- `DECISIONS.template.md` — a skeleton for your decisions log. Replace the prompts with your
  actual reasoning.
- `.gitignore` — a generic starting point.

Suggested (not required) shape for your submission repo:

```
your-repo/
├── README.md            # how to run it from a clean clone
├── DECISIONS.md         # assumptions, definitions, trade-offs, what you cut, known issues
├── RND_MEMO.md          # ≤1 page: the capability you'd build next + who pays for it
├── WALKTHROUGH.md       # optional if you record a video instead
├── summary.json         # machine-readable results (keys must match the brief)
├── data/                # the provided CSVs (or load them from wherever you place them)
├── backend/             # your API / processing
└── frontend/            # your dashboard
```

We suggested React/TypeScript + Python or Node, but choose what lets you do your best work in
the time. Commit as you go.

# MY WORK HERE


| Setup Project |  | 
|:----------------------------------------------------|:----------------------------------------------------------------|
| Paste your 6 .csv files here | /yours_robotics/data | 
| Paste .env file here | /yours_robotics/backend/.env | 


| Setup Backend |  | 
|:----------------------------------------------------|:----------------------------------------------------------------|
| Download and install Python 3.12.9 | https://www.python.org/downloads/release/python-3129/ | 
| Run python in backend dir | [cmd] cd backend |
| Create python virtual environment | [cmd] python -m venv .venv |
| Activate python virtual environment | [cmd] .venv\Scripts\activate |
| Install project packages | [cmd] pip install -r requirements.txt |
| Start Backend | [cmd] python app.py |
| Detivate python virtual environment | [cmd] deactivate |


| Setup Frontend |  | 
|:----------------------------------------------------|:----------------------------------------------------------------|
| Download and install NodeJS v26.3.0 | https://nodejs.org/en/download/current | 
| Run Angular in frontend dir | [cmd] cd frontend |
| Install packages | [cmd] npm install | 
| Start Frontend | [cmd] npm start | 

