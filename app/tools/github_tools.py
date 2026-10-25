import os
import re
from github import Github, Auth
from app.core.models import call_llm

RISKY_NAMES = {'.env'}
RISKY_EXTENSIONS = ('.pem', '.key', '.db')
SKIP_FOLDERS = {'venv', '__pycache__', '.git'}
SECRET_PATTERNS = {
    'GitHub token': r'ghp_[A-Za-z0-9]{20,}',
    'Groq key': r'gsk_[A-Za-z0-9]{20,}',
    'AWS key': r'AKIA[0-9A-Z]{16}',
    'Generic secret': r'(api_key|secret|password)\s*=\s*\S+',
}


def scan_secrets(run_dir):
    findings = []
    for folder, subfolders, files in os.walk(run_dir):
        subfolders[:] = [d for d in subfolders if d not in SKIP_FOLDERS]
        for name in files:
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, run_dir)
            if name in RISKY_NAMES or name.endswith(RISKY_EXTENSIONS):
                findings.append({'file': rel, 'type': 'Risky file name'})
                continue
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except OSError:
                continue
            for label, pattern in SECRET_PATTERNS.items():
                if re.search(pattern, text, re.IGNORECASE):
                    findings.append({'file': rel, 'type': label})
    return findings



def ensure_readme(run_dir, request, code):
    exist=os.path.exists(os.path.join(run_dir, 'README.md'))

    if not exist:
        prompt = f"""Write a short README.md in markdown for this project.
        Include: title, what it does, how to run it.
        The code file is named main.py
        Do not add anything else.

        User request:
        {request}

        Code:
        {code}
        """
        _,answer=call_llm(prompt)

        with open(os.path.join(run_dir, 'README.md'), 'w',encoding='utf-8') as file:
            file.write(answer)



def make_repo_name(request, run_id):
    prompt = f"""Give a 2-4 word lowercase slug for a GitHub repo name for this project.
Words joined by hyphens. Reply with only the slug, nothing else.

Request: {request}
"""
    _, answer = call_llm(prompt)
    name = answer.strip().lower().replace(' ', '-')
    name = re.sub(r'[^a-z0-9-]', '', name).strip('-')
    if not name:
        name = 'shipforge-project'
    return name + '-' + run_id[:4]



def push_to_github(run_dir, repo_name, token, secrets_found):
    skip = {item['file'] for item in secrets_found}
    repo = Github(auth=Auth.Token(token)).get_user().create_repo(repo_name, private=True)
    for folder, subfolders, files in os.walk(run_dir):
        subfolders[:] = [d for d in subfolders if d not in SKIP_FOLDERS]
        for name in files:
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, run_dir)
            if rel in skip:
                continue
            with open(path, 'rb') as f:
                content = f.read()
            repo.create_file(rel.replace('\\', '/'), 'Add ' + rel, content)
    return repo.html_url