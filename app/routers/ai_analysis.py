"""Routes API pour l'analyse des données par IA (Mistral via LiteLLM)"""
import json
import re
import time
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routers.analytics import (
    DATASETS,
    _get_dataset,
    _query_clients_activity,
)

router = APIRouter(prefix="/ai", tags=["Analyse IA"])

SYSTEM_PROMPT = (
    "Tu es un analyste de données expert en assurance construction (dommages-ouvrage, "
    "décennale, tous risques chantier). Tu reçois des agrégats statistiques issus d'un "
    "entrepôt de données fictif. Réponds en français, en Markdown, de façon structurée : "
    "1) synthèse, 2) constats clés chiffrés, 3) anomalies ou points d'attention, "
    "4) recommandations. Base-toi uniquement sur les données fournies et ne fabrique aucun chiffre."
)

RESPONSE_TYPES = {
    "text": "",
    "chart": (
        "\n\nFORMAT DE RÉPONSE OBLIGATOIRE : réponds uniquement par un objet JSON valide (sans Markdown autour) "
        "décrivant UN graphique, avec exactement cette structure :\n"
        '{"title": "titre du graphique", "chart_type": "bar" | "line" | "pie" | "doughnut", '
        '"labels": ["libellé 1", "..."], '
        '"datasets": [{"label": "nom de la série", "data": [nombre, ...]}], '
        '"commentary": "2 à 4 phrases en Markdown qui interprètent le graphique"}\n'
        "Règles : chaque série contient autant de valeurs numériques que de labels ; utilise \"line\" pour une évolution "
        "dans le temps, \"pie\" ou \"doughnut\" pour une répartition (une seule série), \"bar\" sinon ; "
        "pas plus de 15 labels ; les valeurs proviennent exclusivement des données fournies."
    ),
    "table": (
        "\n\nFORMAT DE RÉPONSE OBLIGATOIRE : réponds uniquement par un objet JSON valide (sans Markdown autour) "
        "décrivant UN tableau, avec exactement cette structure :\n"
        '{"title": "titre du tableau", "columns": ["colonne 1", "..."], '
        '"rows": [["valeur", 12.5, "..."]], '
        '"commentary": "2 à 4 phrases en Markdown qui résument les points saillants du tableau"}\n'
        "Règles : chaque ligne contient autant de cellules que de colonnes ; les nombres sont de vrais nombres JSON "
        "(sans unité ni séparateur de milliers, l'unité va dans le nom de la colonne) ; "
        "pas plus de 30 lignes ; les valeurs proviennent exclusivement des données fournies."
    ),
}

DEFAULT_QUESTIONS = {
    "text": "Analyse ces données et dégage les principaux enseignements.",
    "chart": "Propose le graphique le plus pertinent pour illustrer ces données.",
    "table": "Propose un tableau de synthèse pertinent de ces données.",
}

DEFAULT_QUESTION = "Analyse ces données et dégage les principaux enseignements."


class AIAnalysisRequest(BaseModel):
    dataset_key: str
    relations: list[str] = Field(default_factory=list, description="Clés des jointures à appliquer")
    group_by: list[str] = Field(default_factory=list, max_length=2, description="Dimensions 'source.champ' de croisement")
    question: Optional[str] = Field(None, max_length=2000)
    response_type: Literal["text", "chart", "table"] = "text"
    model: Optional[str] = None
    top_n: int = Field(10, ge=3, le=30)


def _llm_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if settings.LITELLM_API_KEY:
        headers["Authorization"] = f"Bearer {settings.LITELLM_API_KEY}"
    return headers


def _bucket_stats(count: int, measure_labels: list[str], values) -> dict | int:
    """Effectif d'une modalité, avec somme et moyenne de chaque mesure (sans mesure : l'effectif seul)"""
    if not measure_labels:
        return count
    stats = {"nombre": count}
    for i, label in enumerate(measure_labels):
        total, average = values[2 * i], values[2 * i + 1]
        stats[f"somme {label}"] = round(float(total or 0), 2)
        stats[f"moyenne {label}"] = round(float(average or 0), 2)
    return stats


def _discover_relations() -> dict:
    """Déduire les jointures possibles des clés étrangères entre sources de données du modèle"""
    table_to_key = {
        d["model"].__table__.name: key for key, d in DATASETS.items() if d.get("model") is not None
    }
    relations = {}
    for child_key, dataset in DATASETS.items():
        if dataset.get("model") is None:
            continue
        for fk in dataset["model"].__table__.foreign_keys:
            parent_key = table_to_key.get(fk.column.table.name)
            if not parent_key or parent_key == child_key:
                continue
            key = f"{child_key}.{fk.parent.name}"
            relations[key] = {
                "key": key,
                "child": child_key,
                "parent": parent_key,
                "column": fk.parent.name,
                "label": f"{DATASETS[child_key]['label']} → {DATASETS[parent_key]['label']} ({fk.parent.name})",
                "child_column": fk.parent,
                "parent_column": fk.column,
            }
    return relations


def _plan_joins(base_key: str, relation_keys: list[str]):
    """Ordonner les jointures à partir de la source principale (les relations cycliques deviennent des filtres)"""
    available = _discover_relations()
    unknown = [k for k in relation_keys if k not in available]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Jointure inconnue : {', '.join(unknown)}")

    included = [base_key]
    joins, extra_filters = [], []
    pending = [available[k] for k in dict.fromkeys(relation_keys)]
    while pending:
        progressed = False
        for rel in list(pending):
            child_in, parent_in = rel["child"] in included, rel["parent"] in included
            if child_in and parent_in:
                extra_filters.append(
                    or_(rel["child_column"].is_(None), rel["child_column"] == rel["parent_column"])
                )
            elif child_in or parent_in:
                new_key = rel["parent"] if child_in else rel["child"]
                joins.append((DATASETS[new_key]["model"], rel["child_column"] == rel["parent_column"]))
                included.append(new_key)
            else:
                continue
            pending.remove(rel)
            progressed = True
        if not progressed:
            labels = ", ".join(r["label"] for r in pending)
            raise HTTPException(status_code=400, detail=f"Jointure(s) non reliée(s) à la source principale : {labels}")
    return included, joins, extra_filters


def _build_joined_summary(db: Session, request: AIAnalysisRequest) -> dict:
    """Résumé agrégé d'une source principale enrichie par des jointures (clés étrangères)"""
    base = _get_dataset(request.dataset_key)
    if base.get("model") is None:
        raise HTTPException(status_code=400, detail="Cette source ne supporte pas les jointures")
    included, joins, extra_filters = _plan_joins(request.dataset_key, request.relations)
    base_model = base["model"]

    def query(*columns):
        q = db.query(*columns).select_from(base_model)
        for model, onclause in joins:
            q = q.outerjoin(model, onclause)
        for condition in extra_filters:
            q = q.filter(condition)
        return q

    dimensions, measures = {}, {}
    for key in included:
        dataset = DATASETS[key]
        for dim in dataset["dimensions"]:
            dimensions[f"{key}.{dim['key']}"] = (f"{dataset['label']} · {dim['label']}", getattr(dataset["model"], dim["key"]))
        for measure in dataset["measures"]:
            measures[f"{key}.{measure['key']}"] = (f"{dataset['label']} · {measure['label']}", getattr(dataset["model"], measure["key"]))

    invalid = [g for g in request.group_by if g not in dimensions]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Dimension de croisement invalide : {', '.join(invalid)}")

    summary = {
        "source": " + ".join(DATASETS[k]["label"] for k in included),
        "jointures": [DATASETS_REL["label"] for DATASETS_REL in _discover_relations().values() if DATASETS_REL["key"] in request.relations],
        "note": "Les jointures sont de type LEFT JOIN depuis la source principale ; les valeurs des tables jointes sont "
                "répétées pour chaque ligne enfant (somme et moyenne portent sur les lignes jointes).",
        "nombre_de_lignes_jointes": query(func.count(base_model.id)).scalar(),
    }

    measure_stats = {}
    for label, column in measures.values():
        row = query(func.count(column), func.sum(column), func.avg(column), func.min(column), func.max(column)).one()
        measure_stats[label] = {
            "renseignes": row[0], "somme": float(row[1] or 0), "moyenne": round(float(row[2] or 0), 2),
            "min": float(row[3] or 0), "max": float(row[4] or 0),
        }
    if measure_stats:
        summary["mesures"] = measure_stats

    distributions = {}
    for label, column in dimensions.values():
        measure_cols = [col for _, col in measures.values()]
        rows = (
            query(column, func.count(base_model.id), *[f(c) for c in measure_cols for f in (func.sum, func.avg)])
            .filter(column.isnot(None))
            .group_by(column).order_by(func.count(base_model.id).desc()).limit(request.top_n).all()
        )
        distributions[label] = {
            str(r[0]): _bucket_stats(r[1], [lbl for lbl, _ in measures.values()], r[2:]) for r in rows
        }
    if distributions:
        summary["repartitions"] = distributions

    if request.group_by:
        group_cols = [dimensions[g][1] for g in request.group_by]
        group_labels = [dimensions[g][0] for g in request.group_by]
        agg_cols, agg_labels = [], []
        for label, column in measures.values():
            agg_cols += [func.sum(column), func.avg(column)]
            agg_labels += [f"somme {label}", f"moyenne {label}"]
        rows = (
            query(*group_cols, func.count(base_model.id), *agg_cols)
            .group_by(*group_cols).order_by(func.count(base_model.id).desc()).limit(request.top_n * 3).all()
        )
        crossing = []
        for r in rows:
            entry = {lbl: (None if v is None else str(v)) for lbl, v in zip(group_labels, r[:len(group_cols)])}
            entry["nombre_de_lignes"] = r[len(group_cols)]
            for lbl, v in zip(agg_labels, r[len(group_cols) + 1:]):
                entry[lbl] = None if v is None else round(float(v), 2)
            crossing.append(entry)
        summary[f"croisement par {' x '.join(group_labels)}"] = crossing

    return summary


def _build_dataset_summary(db: Session, request: AIAnalysisRequest) -> dict:
    """Construire un résumé agrégé (sans données nominatives) d'une source de données"""
    dataset_key, top_n = request.dataset_key, request.top_n
    dataset = _get_dataset(dataset_key)
    if request.relations or request.group_by:
        return _build_joined_summary(db, request)

    if dataset_key == "clients_activity":
        result = _query_clients_activity(db, top_n)
        return {
            "source": dataset["label"],
            "top_clients_anonymises": [
                {"client": f"Client #{i + 1}", **{s["label"]: s["values"][i] for s in result["series"]}}
                for i in range(len(result["labels"]))
            ],
        }

    model = dataset["model"]
    summary = {"source": dataset["label"], "total_enregistrements": db.query(func.count(model.id)).scalar()}

    measure_stats = {}
    for measure in dataset["measures"]:
        column = getattr(model, measure["key"])
        row = db.query(
            func.count(column), func.sum(column), func.avg(column), func.min(column), func.max(column)
        ).one()
        measure_stats[measure["label"]] = {
            "renseignes": row[0],
            "somme": float(row[1] or 0),
            "moyenne": round(float(row[2] or 0), 2),
            "min": float(row[3] or 0),
            "max": float(row[4] or 0),
        }
    if measure_stats:
        summary["mesures"] = measure_stats

    distributions = {}
    for dim in dataset["dimensions"]:
        column = getattr(model, dim["key"])
        measure_cols = [getattr(model, m["key"]) for m in dataset["measures"]]
        rows = (
            db.query(column, func.count(model.id), *[f(c) for c in measure_cols for f in (func.sum, func.avg)])
            .filter(column.isnot(None))
            .group_by(column)
            .order_by(func.count(model.id).desc())
            .limit(top_n)
            .all()
        )
        distributions[dim["label"]] = {
            str(r[0]): _bucket_stats(r[1], [m["label"] for m in dataset["measures"]], r[2:]) for r in rows
        }
    if distributions:
        summary["repartitions"] = distributions

    time_field = dataset.get("time_field")
    if time_field:
        column = getattr(model, time_field["key"])
        bucket = func.date_trunc("month", column)
        rows = (
            db.query(bucket.label("bucket"), func.count(model.id).label("n"))
            .filter(column.isnot(None))
            .group_by(bucket)
            .order_by(bucket.desc())
            .limit(24)
            .all()
        )
        summary[f"evolution_mensuelle ({time_field['label']})"] = {
            r.bucket.strftime("%Y-%m"): r.n for r in reversed(rows)
        }

    return summary


def _parse_structured(text: str, response_type: str):
    """Extraire et valider la réponse JSON d'un graphique ou d'un tableau ; None si invalide"""
    if response_type == "text":
        return None
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start:end + 1])
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None

    if response_type == "chart":
        labels, datasets = data.get("labels"), data.get("datasets")
        if not isinstance(labels, list) or not isinstance(datasets, list) or not datasets:
            return None
        for ds in datasets:
            if not isinstance(ds, dict) or not isinstance(ds.get("data"), list):
                return None
            ds["data"] = [v if isinstance(v, (int, float)) else None for v in ds["data"]]
        if data.get("chart_type") not in ("bar", "line", "pie", "doughnut"):
            data["chart_type"] = "bar"
    else:
        columns, rows = data.get("columns"), data.get("rows")
        if not isinstance(columns, list) or not isinstance(rows, list):
            return None
        if any(not isinstance(r, list) for r in rows):
            return None
    return data


def _extract_text(content) -> str:
    """Le contenu peut être une chaîne ou une liste de blocs (modèles à raisonnement)"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


def _strip_code_fence(text: str) -> str:
    """Retirer l'enveloppe ```markdown ... ``` que certains modèles ajoutent autour de leur réponse"""
    match = re.fullmatch(r"\s*```(?:markdown|md)?\s*\n(.*?)\n```\s*", text, flags=re.DOTALL)
    return match.group(1) if match else text


@router.get("/relations")
def list_relations():
    """Lister les jointures possibles entre sources de données (clés étrangères du modèle)"""
    return [
        {k: v for k, v in r.items() if k not in ("child_column", "parent_column")}
        for r in _discover_relations().values()
    ]


@router.get("/models")
async def list_models():
    """Lister les modèles Mistral exposés par le proxy LiteLLM"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{settings.LITELLM_BASE_URL}/v1/models", headers=_llm_headers())
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Proxy IA injoignable : {e}")

    ids = sorted(m["id"] for m in response.json().get("data", []))
    non_chat = ("embed", "ocr", "moderation", "voxtral", "tts", "transcribe", "fim")
    chat = [i for i in ids if i.startswith("mistral/") and not any(k in i for k in non_chat)]
    return {"models": chat or ids, "default": settings.LITELLM_MODEL}


@router.post("/analyze")
async def analyze(request: AIAnalysisRequest, db: Session = Depends(get_db)):
    """Analyser une source de données avec un modèle Mistral via LiteLLM"""
    summary = _build_dataset_summary(db, request)
    model = request.model or settings.LITELLM_MODEL
    question = (request.question or "").strip() or DEFAULT_QUESTIONS[request.response_type]

    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT + RESPONSE_TYPES[request.response_type]},
            {
                "role": "user",
                "content": f"Données agrégées (JSON) :\n```json\n{json.dumps(summary, ensure_ascii=False, default=str)}\n```\n\nQuestion : {question}",
            },
        ],
    }
    if request.response_type != "text":
        payload["response_format"] = {"type": "json_object"}

    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=settings.LITELLM_TIMEOUT) as client:
            response = await client.post(
                f"{settings.LITELLM_BASE_URL}/v1/chat/completions", headers=_llm_headers(), json=payload
            )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Proxy IA injoignable : {e}")

    if response.status_code != 200:
        try:
            detail = response.json().get("error", {}).get("message") or response.text
        except ValueError:
            detail = response.text
        raise HTTPException(status_code=502, detail=f"Erreur du proxy IA ({response.status_code}) : {detail[:500]}")

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    data = response.json()
    message = data["choices"][0]["message"]
    analysis = _strip_code_fence(_extract_text(message.get("content")))
    return {
        "request": payload,
        "elapsed_ms": elapsed_ms,
        "response_type": request.response_type,
        "structured": _parse_structured(analysis, request.response_type),
        "analysis": analysis,
        "model": data.get("model", model),
        "usage": data.get("usage"),
        "data_summary": summary,
    }
