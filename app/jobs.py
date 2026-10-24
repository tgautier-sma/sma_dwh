"""Exécution en arrière-plan des scripts de génération, avec suivi de progression"""
import os
import json
import re
import subprocess
import threading
import time
import uuid
from collections import deque
from typing import Optional

MAX_LOG_LINES = 400

# (motif, nombre d'éléments déjà terminés) : "Client 3/10" signale que 2 clients sont terminés
_PROGRESS_PATTERNS = [
    (re.compile(r"(?:Client|Sinistre) (\d+)/(\d+)"), lambda i: i - 1),
]
_SQL_NOISE = re.compile(r"^(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|JOIN|LEFT|LIMIT|ORDER|GROUP|AND|OR|VALUES|RETURNING|BEGIN|COMMIT|ROLLBACK|SET|\[|\(|\)|INFO|\d+ )", re.I)
_TOTAL_DAYS_PATTERN = re.compile(r"\((\d+) jours ouvrés")


class Job:
    def __init__(self, label: str, cmd: list, success_message: str, timeout: int):
        self.id = uuid.uuid4().hex[:12]
        self.label = label
        self.cmd = cmd
        self.success_message = success_message
        self.timeout = timeout
        self.status = "running"  # running | success | error
        self.percent: Optional[float] = None  # None : durée indéterminée
        self.step = "Démarrage..."
        self.plan: dict = {}      # volume prévu
        self.counts: dict = {}    # volume déjà créé
        self.message = ""
        self.lines = deque(maxlen=MAX_LOG_LINES)
        self.started_at = time.time()
        self.finished_at: Optional[float] = None

    def to_dict(self, include_output: bool = True) -> dict:
        end = self.finished_at or time.time()
        data = {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "percent": self.percent,
            "step": self.step,
            "message": self.message,
            "elapsed_seconds": round(end - self.started_at, 1),
            "plan": self.plan,
            "counts": self.counts,
        }
        if include_output:
            data["output"] = "\n".join(self.lines)
        return data


_jobs: dict[str, Job] = {}
_lock = threading.Lock()


def current_job() -> Optional[Job]:
    """Tâche en cours, sinon la plus récente"""
    with _lock:
        if not _jobs:
            return None
        running = [j for j in _jobs.values() if j.status == "running"]
        pool = running or list(_jobs.values())
        return max(pool, key=lambda j: j.started_at)


def get_job(job_id: str) -> Optional[Job]:
    with _lock:
        return _jobs.get(job_id)


def start_job(label: str, cmd: list, success_message: str, timeout: int) -> Job:
    """Démarre une tâche ; lève RuntimeError si une autre génération est déjà en cours"""
    with _lock:
        if any(j.status == "running" for j in _jobs.values()):
            raise RuntimeError("Une génération est déjà en cours, attendez sa fin.")
        job = Job(label, cmd, success_message, timeout)
        _jobs[job.id] = job
        # Conserver uniquement les dernières tâches
        for old in sorted(_jobs.values(), key=lambda j: j.started_at)[:-10]:
            _jobs.pop(old.id, None)
    threading.Thread(target=_run, args=(job,), daemon=True).start()
    return job


_ITEM_UNITS = {"Client": "clients", "Sinistre": "sinistres"}


def _handle_structured(job: Job, stripped: str):
    tag, _, payload = stripped[2:].partition(" ")
    try:
        data = json.loads(payload)
    except ValueError:
        return
    if tag == "PLAN":
        job.plan.update(data)
        if data.get("days") is not None:
            job.percent = 0.0
            job.step = f"{data['days']} jours ouvrés à traiter, ~{data.get('expected_visits', 0)} visites prévues"
        elif data.get("reps") is not None:
            job.step = f"Création de {data['reps']} commerciaux"
    elif tag == "PROGRESS":
        job.counts.update({k: v for k, v in data.items() if k not in ("days", "percent")})
        if data.get("percent") is not None:
            job.percent = data["percent"]
        if data.get("days"):
            job.step = f"Jour {data['day']}/{data['days']}"


def _update_progress(job: Job, line: str):
    stripped = line.strip()
    if not stripped:
        return
    if stripped.startswith("##"):
        _handle_structured(job, stripped)
        return
    item = re.search(r"(Client|Sinistre) (\d+)/(\d+)", stripped)
    if item:
        unit = _ITEM_UNITS[item.group(1)]
        job.plan[unit] = int(item.group(3))
        job.counts[unit] = int(item.group(2)) - 1
    for pattern, done_of in _PROGRESS_PATTERNS:
        match = pattern.search(stripped)
        if match:
            index, total = int(match.group(1)), int(match.group(2))
            if total > 0:
                job.percent = round(min(100.0, max(0.0, done_of(index) / total * 100)), 1)
            job.step = stripped.rstrip(":")
            return
    if not job.plan.get("days") and not stripped.startswith("=") and not _SQL_NOISE.match(stripped) and "%(" not in stripped:
        job.step = stripped[:160]


def _run(job: Job):
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    try:
        proc = subprocess.Popen(
            job.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env
        )
    except Exception as e:
        job.status, job.message, job.finished_at = "error", f"Impossible de lancer le script : {e}", time.time()
        return

    timed_out = threading.Event()

    def on_timeout():
        timed_out.set()
        proc.kill()

    timer = threading.Timer(job.timeout, on_timeout)
    timer.start()
    try:
        for line in proc.stdout:
            line = line.rstrip("\n")
            # Les traces SQL (echo SQLAlchemy) ne sont pas utiles à l'utilisateur
            if "sqlalchemy.engine" in line:
                continue
            _update_progress(job, line)
            if not line.startswith("##"):
                job.lines.append(line)
        proc.wait()
    finally:
        timer.cancel()

    output = "\n".join(job.lines)
    if timed_out.is_set():
        job.status, job.message = "error", "La génération a pris trop de temps (timeout)"
    elif proc.returncode != 0 or "❌ Erreur" in output:
        error_line = next((l for l in reversed(job.lines) if "❌" in l), "Erreur lors de la génération")
        job.status, job.message = "error", error_line.strip()
    else:
        for unit, total in job.plan.items():
            if unit in ("clients", "sinistres"):
                job.counts[unit] = total
        job.status, job.message, job.percent = "success", job.success_message, 100.0
        job.step = "Terminé"
    job.finished_at = time.time()
