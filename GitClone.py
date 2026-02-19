#!/usr/bin/env python3
"""
clone_project.py  -  Clone two GitHub repos into a structured project folder.

Usage:
    python clone_project.py
"""

import os
import sys
import subprocess
import platform
import shutil

# -- ANSI colors --------------------------------------------------------------
IS_WIN = platform.system() == "Windows"

def _enable_win_ansi():
    if IS_WIN:
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass

_enable_win_ansi()

def _c(code: str, text: str) -> str:
    return f"{code}{text}\033[0m"

CYAN   = lambda t: _c("\033[96m",  t)
GREEN  = lambda t: _c("\033[92m",  t)
YELLOW = lambda t: _c("\033[93m",  t)
RED    = lambda t: _c("\033[91m",  t)
BOLD   = lambda t: _c("\033[1m",   t)
DIM    = lambda t: _c("\033[2m",   t)

# -- Helpers ------------------------------------------------------------------

def banner():
    print(f"""
{BOLD('╔══════════════════════════════════════════╗')}
{BOLD('║       GitHub Project Cloner              ║')}
{BOLD('║   frontend  .  backend  .  Supabase      ║')}
{BOLD('╚══════════════════════════════════════════╝')}
""", flush=True)

def prompt(label: str, default: str = "", secret: bool = False) -> str:
    suffix = f" {DIM(f'[{default}]')}" if default else ""
    marker = YELLOW("→")
    if secret:
        import getpass
        value = getpass.getpass(f"  {marker} {label}{suffix}: ").strip()
    else:
        value = input(f"  {marker} {label}{suffix}: ").strip()
    return value if value else default

def confirm(label: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    raw = input(f"  {YELLOW('→')} {label} {DIM(f'[{hint}]')}: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes")

def die(msg: str):
    print(f"\n  {RED('✖  ' + msg)}\n", flush=True)
    sys.exit(1)

def success(msg: str):
    print(f"  {GREEN('✔')}  {msg}", flush=True)

def info(msg: str):
    print(f"  {CYAN('·')}  {msg}", flush=True)

def section(title: str):
    print(f"\n{BOLD(f'── {title} ' + '─' * max(0, 44 - len(title)))}\n")

# -- Git helpers --------------------------------------------------------------

def check_git():
    if not shutil.which("git"):
        die("git is not installed or not on your PATH.")

def normalise_repo_url(raw: str) -> str:
    """Accept any of these forms and return a clean HTTPS clone URL:
        https://github.com/user/repo
        https://github.com/user/repo.git
        git@github.com:user/repo.git
        user/repo
        user/repo.git
    """
    raw = raw.strip().rstrip("/")

    # SSH -> HTTPS
    if raw.startswith("git@github.com:"):
        path = raw[len("git@github.com:"):]
        raw = f"https://github.com/{path}"

    # Bare "user/repo" with no scheme
    if not raw.startswith("http"):
        raw = f"https://github.com/{raw}"

    # Ensure .git suffix
    if not raw.endswith(".git"):
        raw += ".git"

    return raw

def repo_name_from_url(url: str) -> str:
    """Extract repo name (without .git) from a clone URL."""
    return url.rstrip("/").rstrip(".git").split("/")[-1].replace(".git", "")

def clone_repo(url: str, dest: str, label: str):
    """Clone url into dest. dest must not already exist."""
    info(f"Cloning {CYAN(url)}")
    info(f"  into  {CYAN(dest)}")

    result = subprocess.run(
        ["git", "clone", url, dest],
        text=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        die(f"Failed to clone {label} repo.\n"
            f"  Make sure the URL is correct and the repo is publicly accessible\n"
            f"  (or that you have SSH credentials set up for private repos).")

    success(f"{label} repo cloned successfully.")

# -- Supabase env writers -----------------------------------------------------

def _env_block(url: str, anon: str, service: str) -> str:
    return (
        f"SUPABASE_URL={url}\n"
        f"SUPABASE_ANON_KEY={anon}\n"
        f"SUPABASE_SERVICE_ROLE_KEY={service}\n"
    )

def _env_example_block() -> str:
    return (
        "SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co\n"
        "SUPABASE_ANON_KEY=your_anon_key\n"
        "SUPABASE_SERVICE_ROLE_KEY=your_service_role_key\n"
    )

def write_env_files(backend_dir: str, url: str, anon: str, service: str):
    """Write .env and .env.example into the backend directory."""
    env_path     = os.path.join(backend_dir, ".env")
    example_path = os.path.join(backend_dir, ".env.example")

    # .env  (real values)
    mode = "a" if os.path.exists(env_path) else "w"
    with open(env_path, mode, encoding="utf-8") as f:
        if mode == "a":
            f.write("\n# Supabase (added by clone_project.py)\n")
        f.write(_env_block(url, anon, service))
    success(f"Written {GREEN('.env')} in backend/")

    # .env.example  (placeholder values)
    mode = "a" if os.path.exists(example_path) else "w"
    with open(example_path, mode, encoding="utf-8") as f:
        if mode == "a":
            f.write("\n# Supabase\n")
        f.write(_env_example_block())
    success(f"Written {GREEN('.env.example')} in backend/")

def update_gitignore(backend_dir: str):
    """Make sure .env is in the backend .gitignore."""
    gitignore_path = os.path.join(backend_dir, ".gitignore")

    existing = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, encoding="utf-8") as f:
            existing = f.read()

    entries_needed = []
    for entry in [".env", "*.env"]:
        if entry not in existing:
            entries_needed.append(entry)

    if entries_needed:
        with open(gitignore_path, "a", encoding="utf-8") as f:
            f.write("\n# Environment files\n")
            for e in entries_needed:
                f.write(f"{e}\n")
        success(f"Updated {GREEN('.gitignore')} in backend/ (.env entries added)")
    else:
        info(".gitignore already ignores .env files — no changes needed.")

def write_readme(root: str, project_name: str, fe_url: str, be_url: str, be_name: str, fe_name: str):
    readme = os.path.join(root, "README.md")
    with open(readme, "w", encoding="utf-8") as f:
        f.write(f"""# {project_name}

A full-stack project assembled from two GitHub repositories.

## Structure

```
{project_name}/
├── frontend/   # {fe_url}
└── backend/    # {be_url}
```

## Setup

### Frontend (`frontend/`)
Refer to the original repo for setup instructions:
- {fe_url}

### Backend (`backend/`)
Refer to the original repo for setup instructions:
- {be_url}

> A `.env` file has been created in `backend/` with your Supabase credentials.
> See `backend/.env.example` for the expected format.
> **Never commit `.env` to version control.**
""")
    success(f"Written {GREEN('README.md')} in project root.")

# -- Main ---------------------------------------------------------------------

def main():
    banner()
    check_git()

    # -- Project name & location ----------------------------------------------
    section("Project Setup")
    project_name = prompt("Project name", "my-app")
    output_dir   = prompt("Where to create the project (leave blank for current directory)", ".")
    root         = os.path.join(os.path.abspath(output_dir), project_name)

    if os.path.exists(root):
        overwrite = confirm(
            f"{YELLOW(root)} already exists. Continue and place repos inside it?",
            default=False,
        )
        if not overwrite:
            print("  Aborted.")
            sys.exit(0)
    else:
        os.makedirs(root)

    # -- Repo URLs ------------------------------------------------------------
    section("GitHub Repository URLs")
    print(f"  {DIM('Accepted formats:')}")
    print(f"  {DIM('  https://github.com/user/repo')}")
    print(f"  {DIM('  git@github.com:user/repo.git')}")
    print(f"  {DIM('  user/repo')}\n")

    fe_raw = prompt("Frontend repo URL")
    if not fe_raw:
        die("Frontend repo URL is required.")
    fe_url = normalise_repo_url(fe_raw)

    be_raw = prompt("Backend repo URL")
    if not be_raw:
        die("Backend repo URL is required.")
    be_url = normalise_repo_url(be_raw)

    fe_name = repo_name_from_url(fe_url)
    be_name = repo_name_from_url(be_url)

    # -- Supabase credentials -------------------------------------------------
    section("Supabase Configuration")
    print(f"  {CYAN('Find these in your Supabase project -> Settings -> API')}\n")

    supabase_url     = prompt("Supabase Project URL  (https://xxxx.supabase.co)")
    supabase_anon    = prompt("Supabase Anon / Public Key")
    supabase_service = prompt("Supabase Service Role Key", secret=True)

    if not supabase_url or not supabase_anon or not supabase_service:
        die("All three Supabase values are required.")

    # -- Clone ----------------------------------------------------------------
    section("Cloning Repositories")

    frontend_dir = os.path.join(root, "frontend")
    backend_dir  = os.path.join(root, "backend")

    if os.path.exists(frontend_dir):
        info(f"frontend/ already exists — skipping clone.")
    else:
        clone_repo(fe_url, frontend_dir, "Frontend")

    print()

    if os.path.exists(backend_dir):
        info(f"backend/ already exists — skipping clone.")
    else:
        clone_repo(be_url, backend_dir, "Backend")

    # -- Supabase env ---------------------------------------------------------
    section("Writing Supabase Environment Files")
    write_env_files(backend_dir, supabase_url, supabase_anon, supabase_service)
    update_gitignore(backend_dir)

    # -- Root README ----------------------------------------------------------
    section("Finishing Up")
    write_readme(root, project_name, fe_url, be_url, be_name, fe_name)

    # -- Summary --------------------------------------------------------------
    print(f"""
{GREEN(BOLD('╔══════════════════════════════════════════╗'))}
{GREEN(BOLD('║       Project ready!                     ║'))}
{GREEN(BOLD('╚══════════════════════════════════════════╝'))}

  {BOLD('Location:')}   {root}

  {BOLD('Structure:')}
    {CYAN('frontend/')}  ← {fe_url}
    {YELLOW('backend/')}   ← {be_url}

  {BOLD('Supabase .env written to:')}  backend/.env

  {YELLOW('⚠  Never commit backend/.env — it contains secret keys.')}
""", flush=True)


if __name__ == "__main__":
    main()
