# gitClone.py

Clone two existing GitHub repositories into a structured `frontend/` and `backend/` project folder, with Supabase credentials automatically written into the backend.

---

## Requirements

- **Python 3.10+**
- **Git** installed and on your PATH
- A **Supabase** project — [create one free at supabase.com](https://supabase.com)

No third-party Python packages required.

---

## Usage

```bash
python gitClone.py
```

---

## Prompts

| Prompt | Description |
|---|---|
| Project name | Name of the root folder that will be created |
| Output directory | Where to create it (defaults to current directory) |
| Frontend repo URL | GitHub URL of your frontend repository |
| Backend repo URL | GitHub URL of your backend repository |
| Supabase Project URL | Found in Supabase → Settings → API |
| Supabase Anon Key | Public key, safe to expose client-side |
| Supabase Service Role Key | Secret key, server-side only (input is hidden) |

---

## Accepted Repo URL Formats

All of the following are valid — the script normalises them automatically:

```
https://github.com/user/repo
https://github.com/user/repo.git
git@github.com:user/repo.git
user/repo
```

---

## Output Structure

```
my-app/
├── frontend/        # your cloned frontend repo
├── backend/         # your cloned backend repo
│   ├── .env         # Supabase credentials (created/appended)
│   ├── .env.example # placeholder values for teammates
│   └── .gitignore   # .env entry added if missing
└── README.md        # auto-generated project overview
```

---

## What Gets Written After Cloning

**`backend/.env`**
Created if it doesn't exist. If a `.env` is already present in the repo, the Supabase block is appended rather than overwriting the file.

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

**`backend/.env.example`**
Written with placeholder values so teammates know which variables are expected.

**`backend/.gitignore`**
Checked for existing `.env` entries. If missing, they are appended — your credentials won't be accidentally committed.

**`README.md`** (project root)
A generated overview documenting the project name, folder structure, and source repo URLs.

---

## Re-run Safety

If `frontend/` or `backend/` already exist inside the target directory, the clone step is skipped for that folder. All other steps (writing `.env`, updating `.gitignore`) still run normally.

---

## Finding Your Supabase Keys

1. Open your project at [supabase.com](https://supabase.com)
2. Go to **Settings → API**
3. Copy the **Project URL**, **anon / public** key, and **service_role** key

> **Never commit `backend/.env`** — it contains your Service Role Key which grants full database access.
