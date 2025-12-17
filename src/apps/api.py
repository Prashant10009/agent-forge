# src/apps/api.py

import os
import re
import time
from typing import Optional
import traceback
import subprocess

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.core.orchestrator import Orchestrator

# ------------------------------------------------------------------
# Figure out the real repo root, regardless of where uvicorn is run
# ------------------------------------------------------------------
HERE = os.path.dirname(__file__)                       # src/apps
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
# REPO_ROOT should be the folder that contains: src/, data/, etc.

app = FastAPI(title="Agent Forge Cockpit")

# Use REPO_ROOT as the orchestrator workspace_dir
orchestrator = Orchestrator(workspace_dir=REPO_ROOT)

# Project root: src/projects under the repo
PROJECTS_ROOT = os.path.join(REPO_ROOT, "src", "projects")

# Static + uploads dirs
STATIC_DIR = os.path.join(HERE, "static")
UPLOADS_DIR = os.path.join(REPO_ROOT, "uploads")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)


app = FastAPI(title="Agent Forge Cockpit")

# Single orchestrator for the whole server
orchestrator = Orchestrator(workspace_dir=".")

# Paths
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
PROJECTS_ROOT = os.path.join(orchestrator.workspace_dir, "src", "projects")
UPLOADS_DIR = os.path.join(orchestrator.workspace_dir, "uploads")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Serve static files and uploads
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


# ---------- MODELS ---------- #

class ChatRequest(BaseModel):
    message: str


class ProjectChatRequest(BaseModel):
    project: str
    message: str


class RunTestsRequest(BaseModel):
    project: str


# ---------- ROOT / UI ---------- #

@app.get("/")
async def get_index():
    """Serve the cockpit HTML UI."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)


# ---------- PROJECTS ---------- #
PROJECT_SUITES = {
    "doc_extractor_suite": [
        os.path.join(PROJECTS_ROOT, "doc_extractor"),
        os.path.join(PROJECTS_ROOT, "doc_extractor_gui"),
    ]
}

@app.get("/api/projects")
async def list_projects():
    """
    List available projects under src/projects.
    """
    projects = []

    if os.path.isdir(PROJECTS_ROOT):
        for name in sorted(os.listdir(PROJECTS_ROOT)):
            full_path = os.path.join(PROJECTS_ROOT, name)
            if os.path.isdir(full_path):
                rel_path = os.path.relpath(full_path, orchestrator.workspace_dir)
                projects.append({"name": name, "path": rel_path})

    return {"projects": projects}



@app.get("/api/project-files")
async def project_files(project: str):
    """
    List all files under a given project.
    """
    project_root = os.path.join(PROJECTS_ROOT, project)
    if not os.path.isdir(project_root):
        return {"error": f"Project '{project}' not found", "files": []}

    files = []
    for root, dirs, filenames in os.walk(project_root):
        for fn in filenames:
            full_path = os.path.join(root, fn)
            rel_path = os.path.relpath(full_path, orchestrator.workspace_dir)
            files.append(rel_path)

    return {"project": project, "files": sorted(files)}


@app.get("/api/tasks")
async def list_tasks(project: Optional[str] = None, limit: int = 20):
    """
    Show recent tasks from the TaskLog.
    If project is given, filter by file_path prefix matching that project.
    """
    # TaskLog.list_recent should already exist in your codebase.
    tasks = orchestrator.task_log.list_recent(limit=limit)
    project_prefix = None
    if project:
        project_prefix = os.path.join("src", "projects", project)

    filtered = []
    for t in tasks:
        # t is likely a dict already; adjust if your implementation is different
        file_path = t.get("file_path") or ""
        if project_prefix and not file_path.startswith(project_prefix):
            continue
        filtered.append(t)

    return {
        "project": project,
        "tasks": filtered,
    }


# ---------- CHAT (GLOBAL + PROJECT) ---------- #

@app.post("/chat")
async def chat(req: ChatRequest):
    description = req.message.strip()
    if not description:
        return {"error": "Empty message"}

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", description[:40]).strip("_").lower()
    if not slug:
        slug = "snippet"

    file_path = os.path.join("generated", f"{slug}_{int(time.time())}.py")
    full_dir = os.path.join(orchestrator.workspace_dir, os.path.dirname(file_path))
    os.makedirs(full_dir, exist_ok=True)

    try:
        result = orchestrator.generate_file(file_path=file_path, description=description)
    except Exception as e:
        # Print full traceback in your terminal
        traceback.print_exc()
        # Return JSON error so the frontend can show it
        raise HTTPException(status_code=500, detail=f"generate_file failed: {e}")

    reply = (
        f"🌍 Global mode\n"
        f"✅ Generated file at: {file_path}\n\n"
        f"Preview (first 400 chars):\n"
        f"{result.get('preview', '')}"
    )

    return {
        "reply": reply,
        "file_path": file_path,
        "task_id": result.get("task_id"),
    }


# --- PROJECT CHAT --- #

@app.post("/api/project-chat")
async def project_chat(req: ProjectChatRequest):
    description = req.message.strip()
    project_name = req.project.strip()

    if not description:
        return {"error": "Empty message"}

    project_root = os.path.join(PROJECTS_ROOT, project_name)
    if not os.path.isdir(project_root):
        return {"error": f"Project '{project_name}' not found"}

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", description[:40]).strip("_").lower()
    if not slug:
        slug = "note"

    rel_file_path = os.path.join(
        os.path.relpath(project_root, orchestrator.workspace_dir),
        "generated",
        f"{slug}_{int(time.time())}.py",
    )

    full_dir = os.path.join(orchestrator.workspace_dir, os.path.dirname(rel_file_path))
    os.makedirs(full_dir, exist_ok=True)

    enriched_desc = (
        f"[Project: {project_name}]\n"
        f"{description}\n\n"
        f"File should live under this project and integrate cleanly."
    )

    try:
        result = orchestrator.generate_file(
            file_path=rel_file_path,
            description=enriched_desc,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"project_chat failed: {e}")

    reply = (
        f"📂 Project: {project_name}\n"
        f"✅ Generated file at: {rel_file_path}\n\n"
        f"Preview (first 400 chars):\n"
        f"{result.get('preview', '')}"
    )

    return {
        "reply": reply,
        "file_path": rel_file_path,
        "task_id": result.get("task_id"),
        "project": project_name,
    }

# ---------- RUN TESTS ---------- #

@app.post("/api/run-tests")
async def run_tests(req: RunTestsRequest):
    """
    Run pytest for the given project using the test_runner tool.
    """
    project_name = req.project.strip()
    project_root = os.path.join(PROJECTS_ROOT, project_name)
    if not os.path.isdir(project_root):
        return {"error": f"Project '{project_name}' not found"}

    test_runner = orchestrator.tool_registry.get("test_runner")
    if not test_runner:
        return {"error": "test_runner tool not registered on orchestrator"}

    # Adjust keyword if your TestRunnerTool expects a different name
    result = test_runner.run(project_root=project_root)

    reply_lines = [
        f"🧪 Tests for project: {project_name}",
        f"Exit code: {result.get('exit_code')}",
        "",
        "STDOUT:",
        result.get("stdout", "").strip() or "(no output)",
        "",
        "STDERR:",
        result.get("stderr", "").strip() or "(no errors)",
    ]

    return {
        "reply": "\n".join(reply_lines),
        "project": project_name,
        "exit_code": result.get("exit_code"),
        "stdout": result.get("stdout"),
        "stderr": result.get("stderr"),
    }
# ---------- RUN DOC EXTRACTOR GUI ---------- #

@app.post("/api/run-doc-gui")
async def run_doc_gui():
    """
    Launch the doc_extractor_gui Streamlit app as a background process.

    This does NOT open a browser tab (you still do that),
    but it starts the server on http://localhost:8501 by default.
    """
    project_name = "doc_extractor_gui"
    project_root = os.path.join(PROJECTS_ROOT, project_name)

    if not os.path.isdir(project_root):
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")

    # Command to run Streamlit
    cmd = ["streamlit", "run", "app.py"]

    try:
        # Start Streamlit in the background
        subprocess.Popen(cmd, cwd=project_root)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start Streamlit: {e}")

    # Default Streamlit URL; adjust port if you use a custom one
    url = "http://localhost:8501"

    return {
        "message": "doc_extractor_gui started (if streamlit is installed and on PATH).",
        "url": url,
        "project": project_name,
    }


# ---------- UPLOAD SCREENSHOT ---------- #

@app.post("/api/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    project: Optional[str] = Form(None),
):
    """
    Upload a screenshot / image and associate it with a project (or global).
    """
    folder_name = (project or "global").strip() or "global"
    safe_folder = re.sub(r"[^a-zA-Z0-9_\-]+", "_", folder_name)

    project_upload_dir = os.path.join(UPLOADS_DIR, safe_folder)
    os.makedirs(project_upload_dir, exist_ok=True)

    timestamp = int(time.time())
    original_name = file.filename or "upload"
    base, ext = os.path.splitext(original_name)
    safe_base = re.sub(r"[^a-zA-Z0-9_\-]+", "_", base) or "image"
    filename = f"{safe_base}_{timestamp}{ext or '.png'}"

    full_path = os.path.join(project_upload_dir, filename)

    content = await file.read()
    with open(full_path, "wb") as f:
        f.write(content)

    rel_path = os.path.relpath(full_path, orchestrator.workspace_dir)
    url = f"/uploads/{safe_folder}/{filename}"

    return {
        "message": "Image uploaded",
        "project": project or "global",
        "path": rel_path,
        "url": url,
    }
