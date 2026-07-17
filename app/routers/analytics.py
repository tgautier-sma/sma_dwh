"""Routes API pour le tableau de bord statistiques personnalisé"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app import schemas
from app.models import (
    DashboardWidgetModel, ClientModel, ClientAddressModel, ConstructionSiteModel,
    ClientContractModel, ClaimModel, SalesRepModel, ClientVisitModel, InsuranceProposalModel
)

router = APIRouter(prefix="/analytics", tags=["Statistiques"])


# =============================================================================
# REGISTRE DES SOURCES DE DONNÉES DISPONIBLES POUR LES GRAPHIQUES
# =============================================================================

DATASETS = {
    "clients": {
        "label": "Clients",
        "model": ClientModel,
        "dimensions": [
            {"key": "client_type", "label": "Type de client"},
            {"key": "city", "label": "Ville"},
            {"key": "country", "label": "Pays"},
        ],
        "measures": [],
        "time_field": {"key": "created_at", "label": "Date de création"},
    },
    "addresses": {
        "label": "Adresses",
        "model": ClientAddressModel,
        "dimensions": [
            {"key": "address_type", "label": "Type d'adresse"},
            {"key": "city", "label": "Ville"},
            {"key": "region", "label": "Région"},
        ],
        "measures": [
            {"key": "warehouse_surface_m2", "label": "Surface entrepôt (m²)"},
        ],
        "time_field": {"key": "created_at", "label": "Date de création"},
    },
    "sites": {
        "label": "Chantiers",
        "model": ConstructionSiteModel,
        "dimensions": [
            {"key": "building_category_code", "label": "Catégorie de bâtiment"},
            {"key": "work_category_code", "label": "Catégorie de travaux"},
            {"key": "city", "label": "Ville"},
            {"key": "region", "label": "Région"},
        ],
        "measures": [
            {"key": "total_surface_m2", "label": "Surface totale (m²)"},
            {"key": "construction_cost", "label": "Coût de construction (€)"},
            {"key": "total_project_value", "label": "Valeur totale du projet (€)"},
        ],
        "time_field": {"key": "opening_date", "label": "Date d'ouverture"},
    },
    "contracts": {
        "label": "Contrats",
        "model": ClientContractModel,
        "dimensions": [
            {"key": "status", "label": "Statut"},
            {"key": "contract_type_code", "label": "Type de contrat"},
        ],
        "measures": [
            {"key": "annual_premium", "label": "Prime annuelle (€)"},
            {"key": "insured_amount", "label": "Montant assuré (€)"},
        ],
        "time_field": {"key": "effective_date", "label": "Date d'effet"},
    },
    "claims": {
        "label": "Sinistres",
        "model": ClaimModel,
        "dimensions": [
            {"key": "claim_type", "label": "Type de sinistre"},
            {"key": "status", "label": "Statut"},
            {"key": "severity", "label": "Gravité"},
        ],
        "measures": [
            {"key": "estimated_amount", "label": "Montant estimé (€)"},
            {"key": "expert_amount", "label": "Montant expertisé (€)"},
            {"key": "indemnity_amount", "label": "Montant indemnisé (€)"},
        ],
        "time_field": {"key": "declaration_date", "label": "Date de déclaration"},
    },
    "sales_reps": {
        "label": "Commerciaux",
        "model": SalesRepModel,
        "dimensions": [
            {"key": "region", "label": "Région"},
            {"key": "agency", "label": "Agence"},
        ],
        "measures": [],
        "time_field": {"key": "hire_date", "label": "Date d'embauche"},
    },
    "visits": {
        "label": "Visites clients",
        "model": ClientVisitModel,
        "dimensions": [
            {"key": "visit_type", "label": "Type de visite"},
            {"key": "visit_status", "label": "Statut"},
        ],
        "measures": [
            {"key": "duration_minutes", "label": "Durée (min)"},
            {"key": "client_satisfaction", "label": "Satisfaction client"},
        ],
        "time_field": {"key": "visit_date", "label": "Date de visite"},
    },
    "proposals": {
        "label": "Propositions",
        "model": InsuranceProposalModel,
        "dimensions": [
            {"key": "status", "label": "Statut"},
            {"key": "contract_type_code", "label": "Type de contrat"},
        ],
        "measures": [
            {"key": "proposed_annual_premium", "label": "Prime annuelle proposée (€)"},
            {"key": "proposed_insured_amount", "label": "Montant assuré proposé (€)"},
        ],
        "time_field": {"key": "proposal_date", "label": "Date de proposition"},
    },
    "clients_activity": {
        "label": "Activité des clients (contrats / sinistres / chantiers)",
        "multi_measure": True,
        "dimensions": [],
        "measures": [],
        "time_field": None,
        "series": [
            {"key": "num_contracts", "label": "Contrats", "color": "#4a3aa7"},
            {"key": "num_claims", "label": "Sinistres", "color": "#e34948"},
            {"key": "num_sites", "label": "Chantiers", "color": "#eb6834"},
        ],
    },
}

ALLOWED_CHART_TYPES = {"bar", "line", "pie", "doughnut"}
ALLOWED_AGGREGATIONS = {"count", "sum", "avg"}
ALLOWED_GRANULARITIES = {"day", "week", "month", "year"}


@router.get("/datasets")
def list_datasets():
    """Lister les sources de données disponibles et leurs champs pour construire un graphique"""
    return [
        {
            "key": key,
            "label": dataset["label"],
            "dimensions": dataset["dimensions"],
            "measures": dataset["measures"],
            "time_field": dataset.get("time_field"),
            "multi_measure": dataset.get("multi_measure", False),
            "series": dataset.get("series", []),
        }
        for key, dataset in DATASETS.items()
    ]


class AnalyticsQueryRequest(BaseModel):
    dataset_key: str
    chart_type: str
    dimension_field: Optional[str] = None
    time_granularity: Optional[str] = None
    measure_field: Optional[str] = None
    aggregation: str = "count"
    limit: int = Field(10, ge=1, le=50)


def _get_dataset(dataset_key: str) -> dict:
    dataset = DATASETS.get(dataset_key)
    if not dataset:
        raise HTTPException(status_code=400, detail=f"Source de données inconnue : {dataset_key}")
    return dataset


def _resolve_measure_expression(dataset: dict, measure_field: Optional[str], aggregation: str):
    if aggregation not in ALLOWED_AGGREGATIONS:
        raise HTTPException(status_code=400, detail=f"Agrégation invalide : {aggregation}")

    if aggregation == "count":
        return func.count(dataset["model"].id)

    allowed_measures = {m["key"] for m in dataset["measures"]}
    if measure_field not in allowed_measures:
        raise HTTPException(status_code=400, detail=f"Champ de mesure invalide pour cette source : {measure_field}")

    column = getattr(dataset["model"], measure_field)
    agg_func = {"sum": func.sum, "avg": func.avg}[aggregation]
    return agg_func(column)


def _query_clients_activity(db: Session, limit: int):
    """Nombre de contrats, sinistres et chantiers par client (top clients par activité totale)"""
    client_label = func.coalesce(
        ClientModel.company_name,
        func.concat(ClientModel.first_name, ' ', ClientModel.last_name)
    )

    contracts_agg = (
        db.query(
            ClientContractModel.client_id.label("client_id"),
            func.count(ClientContractModel.id).label("num_contracts"),
            func.count(func.distinct(ClientContractModel.construction_site_id)).label("num_sites"),
        )
        .group_by(ClientContractModel.client_id)
        .subquery()
    )

    claims_agg = (
        db.query(
            ClientContractModel.client_id.label("client_id"),
            func.count(ClaimModel.id).label("num_claims"),
        )
        .join(ClaimModel, ClaimModel.contract_id == ClientContractModel.id)
        .group_by(ClientContractModel.client_id)
        .subquery()
    )

    num_contracts = func.coalesce(contracts_agg.c.num_contracts, 0)
    num_sites = func.coalesce(contracts_agg.c.num_sites, 0)
    num_claims = func.coalesce(claims_agg.c.num_claims, 0)

    rows = (
        db.query(
            client_label.label("label"),
            num_contracts.label("num_contracts"),
            num_claims.label("num_claims"),
            num_sites.label("num_sites"),
        )
        .outerjoin(contracts_agg, contracts_agg.c.client_id == ClientModel.id)
        .outerjoin(claims_agg, claims_agg.c.client_id == ClientModel.id)
        .order_by((num_contracts + num_claims + num_sites).desc())
        .limit(limit)
        .all()
    )

    labels = [row.label for row in rows]
    series_meta = DATASETS["clients_activity"]["series"]
    values_by_key = {
        "num_contracts": [float(row.num_contracts) for row in rows],
        "num_claims": [float(row.num_claims) for row in rows],
        "num_sites": [float(row.num_sites) for row in rows],
    }
    series = [
        {**s, "values": values_by_key[s["key"]]}
        for s in series_meta
    ]

    return {"labels": labels, "series": series}


@router.post("/query")
def query_analytics(request: AnalyticsQueryRequest, db: Session = Depends(get_db)):
    """Exécuter une agrégation sur une source de données pour alimenter un graphique"""
    if request.dataset_key == "clients_activity":
        return _query_clients_activity(db, request.limit)

    if request.chart_type not in ALLOWED_CHART_TYPES:
        raise HTTPException(status_code=400, detail=f"Type de graphique inconnu : {request.chart_type}")

    dataset = _get_dataset(request.dataset_key)
    model = dataset["model"]
    measure_expr = _resolve_measure_expression(dataset, request.measure_field, request.aggregation)

    if request.chart_type in ("bar", "pie", "doughnut"):
        allowed_dims = {d["key"] for d in dataset["dimensions"]}
        if request.dimension_field not in allowed_dims:
            raise HTTPException(status_code=400, detail=f"Champ de regroupement invalide : {request.dimension_field}")

        dim_column = getattr(model, request.dimension_field)
        rows = (
            db.query(dim_column.label("bucket"), measure_expr.label("value"))
            .filter(dim_column.isnot(None))
            .group_by(dim_column)
            .order_by(measure_expr.desc())
            .limit(request.limit)
            .all()
        )
        labels = [str(row.bucket) for row in rows]
        values = [float(row.value or 0) for row in rows]

    elif request.chart_type == "line":
        time_field = dataset.get("time_field")
        if not time_field:
            raise HTTPException(status_code=400, detail="Cette source de données n'a pas de champ temporel")

        granularity = request.time_granularity if request.time_granularity in ALLOWED_GRANULARITIES else "month"
        time_column = getattr(model, time_field["key"])
        bucket = func.date_trunc(granularity, time_column)

        rows = (
            db.query(bucket.label("bucket"), measure_expr.label("value"))
            .filter(time_column.isnot(None))
            .group_by(bucket)
            .order_by(bucket.asc())
            .limit(500)
            .all()
        )
        labels = [row.bucket.strftime("%Y-%m-%d") for row in rows]
        values = [float(row.value or 0) for row in rows]

    return {"labels": labels, "values": values}


# =============================================================================
# CRUD WIDGETS (TABLEAU DE BORD SAUVEGARDÉ)
# =============================================================================

@router.get("/widgets", response_model=list[schemas.DashboardWidget])
@router.get("/widgets/", response_model=list[schemas.DashboardWidget])
def list_widgets(db: Session = Depends(get_db)):
    """Lister les widgets du tableau de bord statistiques, dans leur ordre d'affichage"""
    return db.query(DashboardWidgetModel).order_by(DashboardWidgetModel.position.asc()).all()


@router.post("/widgets", response_model=schemas.DashboardWidget, status_code=status.HTTP_201_CREATED)
@router.post("/widgets/", response_model=schemas.DashboardWidget, status_code=status.HTTP_201_CREATED)
def create_widget(widget: schemas.DashboardWidgetCreate, db: Session = Depends(get_db)):
    """Ajouter un widget au tableau de bord statistiques"""
    if widget.dataset_key not in DATASETS:
        raise HTTPException(status_code=400, detail=f"Source de données inconnue : {widget.dataset_key}")
    if widget.chart_type not in ALLOWED_CHART_TYPES:
        raise HTTPException(status_code=400, detail=f"Type de graphique inconnu : {widget.chart_type}")

    max_position = db.query(func.max(DashboardWidgetModel.position)).scalar()
    db_widget = DashboardWidgetModel(
        **widget.model_dump(),
        position=(max_position + 1) if max_position is not None else 0
    )
    db.add(db_widget)
    db.commit()
    db.refresh(db_widget)
    return db_widget


@router.delete("/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_widget(widget_id: int, db: Session = Depends(get_db)):
    """Supprimer un widget du tableau de bord statistiques"""
    db_widget = db.query(DashboardWidgetModel).filter(DashboardWidgetModel.id == widget_id).first()
    if not db_widget:
        raise HTTPException(status_code=404, detail="Widget non trouvé")

    db.delete(db_widget)
    db.commit()
    return None
