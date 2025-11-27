from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
import os
from datetime import date, datetime

from app import models
from app.database import engine, get_db
from app.pdf_utils import build_pdf

# Initialisation
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# ➜ Monter les fichiers statiques
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ➜ Création des tables
models.Base.metadata.create_all(bind=engine)

from datetime import date

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    # Navires à quai
    navires_a_quai = db.query(models.Navire).filter(models.Navire.statut_actuel == "à quai").count()

    # Inspections du mois en cours (du 1er au jour courant)
    today = date.today()
    debut_mois = date(today.year, today.month, 1)
    inspections_mois = db.query(models.Inspection).filter(models.Inspection.date >= debut_mois).count()

    # Marchandises totales
    marchandises_total = db.query(models.Marchandise).count()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "navires_a_quai": navires_a_quai,
        "inspections_mois": inspections_mois,
        "marchandises_total": marchandises_total
    })

# -------------------------
# NAVIRES
# -------------------------

@app.get("/navires", response_class=HTMLResponse)
def list_navires(request: Request, db: Session = Depends(get_db)):
    navires = db.query(models.Navire).all()
    return templates.TemplateResponse("navires.html", {"request": request, "navires": navires})

@app.post("/navires/add")
def add_navire(
    nom: str = Form(...),
    imo: str = Form(...),
    pavillon: str = Form(None),
    annee_construction: int = Form(None),
    tonnage: float = Form(None),
    type: str = Form(None),
    dernier_port: str = Form(None),
    prochaine_destination: str = Form(None),
    statut_actuel: str = Form(None),
    autres: str = Form(None),
    db: Session = Depends(get_db)
):
    navire = models.Navire(
        nom=nom,
        imo=imo,
        pavillon=pavillon,
        annee_construction=annee_construction,
        tonnage=tonnage,
        type=type,
        dernier_port=dernier_port,
        prochaine_destination=prochaine_destination,
        statut_actuel=statut_actuel,
        autres=autres,
    )
    db.add(navire)
    db.commit()
    return RedirectResponse(url="/navires", status_code=303)

@app.post("/navires/{navire_id}/delete")
def delete_navire(navire_id: int, db: Session = Depends(get_db)):
    navire = db.query(models.Navire).filter(models.Navire.id == navire_id).first()
    if navire:
        db.delete(navire)
        db.commit()
    return RedirectResponse(url="/navires", status_code=303)

@app.get("/navires/{navire_id}/edit", response_class=HTMLResponse)
def edit_navire(navire_id: int, request: Request, db: Session = Depends(get_db)):
    navire = db.query(models.Navire).filter(models.Navire.id == navire_id).first()
    if not navire:
        return HTMLResponse(content="<h1>Navire introuvable</h1>", status_code=404)
    return templates.TemplateResponse("navire_edit.html", {"request": request, "navire": navire})

@app.post("/navires/{navire_id}/update")
def update_navire(
    navire_id: int,
    nom: str = Form(...),
    imo: str = Form(...),
    pavillon: str = Form(None),
    annee_construction: int = Form(None),
    tonnage: float = Form(None),
    type: str = Form(None),
    dernier_port: str = Form(None),
    prochaine_destination: str = Form(None),
    statut_actuel: str = Form(None),
    autres: str = Form(None),
    db: Session = Depends(get_db),
):
    navire = db.query(models.Navire).filter(models.Navire.id == navire_id).first()
    if navire:
        navire.nom = nom
        navire.imo = imo
        navire.pavillon = pavillon
        navire.annee_construction = annee_construction
        navire.tonnage = tonnage
        navire.type = type
        navire.dernier_port = dernier_port
        navire.prochaine_destination = prochaine_destination
        navire.statut_actuel = statut_actuel
        navire.autres = autres
        db.commit()
    return RedirectResponse(url="/navires", status_code=303)

@app.get("/navires/{navire_id}", response_class=HTMLResponse)
def navire_detail(navire_id: int, request: Request, db: Session = Depends(get_db)):
    navire = db.query(models.Navire).filter(models.Navire.id == navire_id).first()
    if not navire:
        return HTMLResponse(content="<h1>Navire introuvable</h1>", status_code=404)
    return templates.TemplateResponse("navire_detail.html", {"request": request, "navire": navire})

@app.get("/navires/{navire_id}/download")
def download_navire(navire_id: int, db: Session = Depends(get_db)):
    navire = db.query(models.Navire).filter(models.Navire.id == navire_id).first()
    if not navire:
        return HTMLResponse(content="<h1>Navire introuvable</h1>", status_code=404)

    file_path = f"navire_{navire.id}.pdf"

    # 🔹 Inclure tous les champs du formulaire
    data = [
        ["Nom", navire.nom],
        ["IMO", navire.imo],
        ["Pavillon", navire.pavillon or "N/A"],
        ["Année de construction", navire.annee_construction or "N/A"],
        ["Tonnage (tonnes)", navire.tonnage or "N/A"],
        ["Type de navire", navire.type or "N/A"],
        ["Dernier port d’escale", navire.dernier_port or "N/A"],
        ["Prochaine destination", navire.prochaine_destination or "N/A"],
        ["Statut actuel", navire.statut_actuel or "N/A"],
        ["Autres informations", navire.autres or "N/A"],
    ]

    # Génération PDF via utilitaire
    build_pdf(file_path, "MarineGab — Fiche navire", data)

    return FileResponse(path=file_path, filename=file_path, media_type="application/pdf")

# -------------------------
# PORTS
# -------------------------

@app.get("/ports", response_class=HTMLResponse)
def list_ports(request: Request, db: Session = Depends(get_db)):
    ports = db.query(models.Port).all()
    return templates.TemplateResponse("ports.html", {"request": request, "ports": ports})

@app.post("/ports/add")
def add_port(
    nom: str = Form(...),
    pays: str = Form(None),
    ville: str = Form(None),
    capacite: float = Form(None),
    type: str = Form(None),
    coordonnees: str = Form(None),
    responsable: str = Form(None),
    db: Session = Depends(get_db),
):
    port = models.Port(
        nom=nom,
        pays=pays,
        ville=ville,
        capacite=capacite,
        type=type,
        coordonnees=coordonnees,
        responsable=responsable,
    )
    db.add(port)
    db.commit()
    return RedirectResponse(url="/ports", status_code=303)

@app.get("/ports/{port_id}/edit", response_class=HTMLResponse)
def edit_port(port_id: int, request: Request, db: Session = Depends(get_db)):
    port = db.query(models.Port).filter(models.Port.id == port_id).first()
    if not port:
        return HTMLResponse(content="<h1>Port introuvable</h1>", status_code=404)
    return templates.TemplateResponse("port_edit.html", {"request": request, "port": port})

@app.post("/ports/{port_id}/update")
def update_port(
    port_id: int,
    nom: str = Form(...),
    pays: str = Form(None),
    ville: str = Form(None),
    capacite: float = Form(None),
    type: str = Form(None),
    coordonnees: str = Form(None),
    responsable: str = Form(None),
    db: Session = Depends(get_db),
):
    port = db.query(models.Port).filter(models.Port.id == port_id).first()
    if port:
        port.nom = nom
        port.pays = pays
        port.ville = ville
        port.capacite = capacite
        port.type = type
        port.coordonnees = coordonnees
        port.responsable = responsable
        db.commit()
    return RedirectResponse(url="/ports", status_code=303)

@app.post("/ports/{port_id}/delete")
def delete_port(port_id: int, db: Session = Depends(get_db)):
    port = db.query(models.Port).filter(models.Port.id == port_id).first()
    if port:
        db.delete(port)
        db.commit()
    return RedirectResponse(url="/ports", status_code=303)

# -------------------------
# -------------------------
# MARCHANDISES
# -------------------------

@app.get("/marchandises", response_class=HTMLResponse)
def list_marchandises(request: Request, db: Session = Depends(get_db)):
    marchandises = db.query(models.Marchandise).all()
    navires = db.query(models.Navire).all()
    return templates.TemplateResponse(
        "marchandises.html",
        {"request": request, "marchandises": marchandises, "navires": navires}
    )

@app.post("/marchandises/add")
def add_marchandise(
    nom: str = Form(...),
    type: str = Form(None),
    poids: float = Form(...),
    volume: float = Form(...),
    tracking_number: str = Form(...),
    navire_id: int = Form(...),
    db: Session = Depends(get_db),
):
    # Vérifier si le tracking_number existe déjà
    existing = db.query(models.Marchandise).filter(models.Marchandise.tracking_number == tracking_number).first()
    if existing:
        return HTMLResponse(
            content=f"<h3>Erreur : le numéro de tracking {tracking_number} existe déjà.</h3>",
            status_code=400
        )

    marchandise = models.Marchandise(
        nom=nom,
        type=type,
        poids=poids,
        volume=volume,
        tracking_number=tracking_number,
        navire_id=navire_id,
    )
    db.add(marchandise)
    db.commit()
    return RedirectResponse(url="/marchandises", status_code=303)

@app.get("/marchandises/{marchandise_id}/edit", response_class=HTMLResponse)
def edit_marchandise(marchandise_id: int, request: Request, db: Session = Depends(get_db)):
    marchandise = db.query(models.Marchandise).filter(models.Marchandise.id == marchandise_id).first()
    navires = db.query(models.Navire).all()
    if not marchandise:
        return HTMLResponse(content="<h1>Marchandise introuvable</h1>", status_code=404)
    return templates.TemplateResponse(
        "marchandise_edit.html",
        {"request": request, "marchandise": marchandise, "navires": navires}
    )

@app.post("/marchandises/{marchandise_id}/update")
def update_marchandise(
    marchandise_id: int,
    nom: str = Form(...),
    type: str = Form(None),
    poids: float = Form(...),
    volume: float = Form(...),
    tracking_number: str = Form(...),
    navire_id: int = Form(...),
    db: Session = Depends(get_db),
):
    marchandise = db.query(models.Marchandise).filter(models.Marchandise.id == marchandise_id).first()
    if marchandise:
        # Vérifier si le nouveau tracking_number est déjà utilisé par un autre
        existing = db.query(models.Marchandise).filter(
            models.Marchandise.tracking_number == tracking_number,
            models.Marchandise.id != marchandise_id
        ).first()
        if existing:
            return HTMLResponse(
                content=f"<h3>Erreur : le numéro de tracking {tracking_number} existe déjà.</h3>",
                status_code=400
            )

        marchandise.nom = nom
        marchandise.type = type
        marchandise.poids = poids
        marchandise.volume = volume
        marchandise.tracking_number = tracking_number
        marchandise.navire_id = navire_id
        db.commit()
    return RedirectResponse(url="/marchandises", status_code=303)

@app.post("/marchandises/{marchandise_id}/delete")
def delete_marchandise(marchandise_id: int, db: Session = Depends(get_db)):
    marchandise = db.query(models.Marchandise).filter(models.Marchandise.id == marchandise_id).first()
    if marchandise:
        db.delete(marchandise)
        db.commit()
    return RedirectResponse(url="/marchandises", status_code=303)

@app.get("/marchandises/{marchandise_id}/download")
def download_marchandise(marchandise_id: int, db: Session = Depends(get_db)):
    marchandise = db.query(models.Marchandise).filter(models.Marchandise.id == marchandise_id).first()
    if not marchandise:
        return HTMLResponse(content="<h1>Marchandise introuvable</h1>", status_code=404)

    # 🔹 Récupérer le navire associé
    navire_nom = "N/A"
    navire_imo = "N/A"
    if marchandise.navire_id:
        navire = db.query(models.Navire).filter(models.Navire.id == marchandise.navire_id).first()
        if navire:
            navire_nom = navire.nom
            navire_imo = navire.imo

    file_path = f"marchandise_{marchandise.id}.pdf"
    data = [
        ["Nom", marchandise.nom],
        ["Type", marchandise.type or "N/A"],
        ["Poids (tonnes)", marchandise.poids],
        ["Volume (m³)", marchandise.volume],
        ["Numéro de tracking", marchandise.tracking_number],
        ["Navire associé", f"{navire_nom} — IMO: {navire_imo}" if navire_nom != "N/A" else "N/A"],
    ]
    build_pdf(file_path, "MarineGab — Fiche marchandise", data)
    return FileResponse(path=file_path, filename=file_path, media_type="application/pdf")

# INSPECTIONS
# -------------------------
@app.get("/inspections", response_class=HTMLResponse)
def list_inspections(request: Request, db: Session = Depends(get_db)):
    inspections = db.query(models.Inspection).all()
    return templates.TemplateResponse("inspections.html", {"request": request, "inspections": inspections})

@app.post("/inspections/add")
def add_inspection(
    date: str = Form(...),
    navire_imo: str = Form(...),
    port_nom: str = Form(...),
    inspecteur: str = Form(...),
    rapport: str = Form(None),
    certificat_securite: str = Form(...),
    certificat_classe: str = Form(...),
    certificat_pollution: str = Form(...),
    brevets_marins: str = Form(...),
    certificats_medicaux: str = Form(...),
    journal_bord: str = Form(...),
    papiers_douaniers: str = Form(...),
    gilets_combinaisons: str = Form(...),
    radeaux_canots: str = Form(...),
    extincteurs: str = Form(...),
    alarmes_detecteurs: str = Form(...),
    systeme_incendie: str = Form(...),
    normes_antipollution: str = Form(...),
    conditions_vie: str = Form(...),
    observations: str = Form(None),
    db: Session = Depends(get_db),
):
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    inspection = models.Inspection(
        date=date_obj,
        navire_imo=navire_imo,
        port_nom=port_nom,
        inspecteur=inspecteur,
        rapport=rapport,
        certificat_securite=certificat_securite,
        certificat_classe=certificat_classe,
        certificat_pollution=certificat_pollution,
        brevets_marins=brevets_marins,
        certificats_medicaux=certificats_medicaux,
        journal_bord=journal_bord,
        papiers_douaniers=papiers_douaniers,
        gilets_combinaisons=gilets_combinaisons,
        radeaux_canots=radeaux_canots,
        extincteurs=extincteurs,
        alarmes_detecteurs=alarmes_detecteurs,
        systeme_incendie=systeme_incendie,
        normes_antipollution=normes_antipollution,
        conditions_vie=conditions_vie,
        observations=observations
    )
    db.add(inspection)
    db.commit()
    return RedirectResponse(url="/inspections", status_code=303)

@app.get("/inspections/{inspection_id}/edit", response_class=HTMLResponse)
def edit_inspection(inspection_id: int, request: Request, db: Session = Depends(get_db)):
    inspection = db.query(models.Inspection).filter(models.Inspection.id == inspection_id).first()
    if not inspection:
        return HTMLResponse(content="<h1>Inspection introuvable</h1>", status_code=404)
    return templates.TemplateResponse("inspection_edit.html", {"request": request, "inspection": inspection})

@app.post("/inspections/{inspection_id}/update")
def update_inspection(
    inspection_id: int,
    date: str = Form(...),
    navire_imo: str = Form(...),
    port_nom: str = Form(...),
    inspecteur: str = Form(...),
    rapport: str = Form(None),
    certificat_securite: str = Form("Non conforme"),
    certificat_classe: str = Form("Non conforme"),
    certificat_pollution: str = Form("Non conforme"),
    brevets_marins: str = Form("Non conforme"),
    certificats_medicaux: str = Form("Non conforme"),
    journal_bord: str = Form("Non conforme"),
    papiers_douaniers: str = Form("Non conforme"),
    gilets_combinaisons: str = Form("Non conforme"),
    radeaux_canots: str = Form("Non conforme"),
    extincteurs: str = Form("Non conforme"),
    alarmes_detecteurs: str = Form("Non conforme"),
    systeme_incendie: str = Form("Non conforme"),
    normes_antipollution: str = Form("Non conforme"),
    conditions_vie: str = Form("Non conforme"),
    observations: str = Form(None),
    db: Session = Depends(get_db),
):
    inspection = db.query(models.Inspection).filter(models.Inspection.id == inspection_id).first()
    if inspection:
        inspection.date = date
        inspection.navire_imo = navire_imo
        inspection.port_nom = port_nom
        inspection.inspecteur = inspecteur
        inspection.rapport = rapport
        inspection.certificat_securite = certificat_securite
        inspection.certificat_classe = certificat_classe
        inspection.certificat_pollution = certificat_pollution
        inspection.brevets_marins = brevets_marins
        inspection.certificats_medicaux = certificats_medicaux
        inspection.journal_bord = journal_bord
        inspection.papiers_douaniers = papiers_douaniers
        inspection.gilets_combinaisons = gilets_combinaisons
        inspection.radeaux_canots = radeaux_canots
        inspection.extincteurs = extincteurs
        inspection.alarmes_detecteurs = alarmes_detecteurs
        inspection.systeme_incendie = systeme_incendie
        inspection.normes_antipollution = normes_antipollution
        inspection.conditions_vie = conditions_vie
        inspection.observations = observations
        db.commit()
    return RedirectResponse(url="/inspections", status_code=303)

@app.post("/inspections/{inspection_id}/delete")
def delete_inspection(inspection_id: int, db: Session = Depends(get_db)):
    inspection = db.query(models.Inspection).filter(models.Inspection.id == inspection_id).first()
    if inspection:
        db.delete(inspection)
        db.commit()
    return RedirectResponse(url="/inspections", status_code=303)

@app.get("/inspections/{inspection_id}", response_class=HTMLResponse)
def inspection_detail(inspection_id: int, request: Request, db: Session = Depends(get_db)):
    inspection = db.query(models.Inspection).filter(models.Inspection.id == inspection_id).first()
    if not inspection:
        return HTMLResponse(content="<h1>Inspection introuvable</h1>", status_code=404)
    return templates.TemplateResponse("inspection_detail.html", {"request": request, "inspection": inspection})

@app.get("/inspections/{inspection_id}/download")
def download_inspection(inspection_id: int, db: Session = Depends(get_db)):
    inspection = db.query(models.Inspection).filter(models.Inspection.id == inspection_id).first()
    if not inspection:
        return HTMLResponse(content="<h1>Inspection introuvable</h1>", status_code=404)

    file_path = f"inspection_{inspection.id}.pdf"
    data = [
        ["Date", inspection.date],
        ["Navire IMO", inspection.navire_imo],
        ["Port", inspection.port_nom],
        ["Inspecteur", inspection.inspecteur],
        ["Rapport", inspection.rapport or "N/A"],
        ["Certificat sécurité", inspection.certificat_securite],
        ["Certificat de classe", inspection.certificat_classe],
        ["Certificat pollution", inspection.certificat_pollution],
        ["Brevets marins", inspection.brevets_marins],
        ["Certificats médicaux", inspection.certificats_medicaux],
        ["Journal de bord", inspection.journal_bord],
        ["Papiers douaniers", inspection.papiers_douaniers],
        ["Gilets & combinaisons", inspection.gilets_combinaisons],
        ["Radeaux & canots", inspection.radeaux_canots],
        ["Extincteurs", inspection.extincteurs],
        ["Alarmes & détecteurs", inspection.alarmes_detecteurs],
        ["Système anti-incendie", inspection.systeme_incendie],
        ["Normes antipollution", inspection.normes_antipollution],
        ["Conditions de vie", inspection.conditions_vie],
        ["Observations", inspection.observations or "Aucune"],
    ]
    build_pdf(file_path, "MarineGab — Fiche inspection", data)
    return FileResponse(path=file_path, filename=file_path, media_type="application/pdf")

# -------------------------
# STATISTIQUES
# -------------------------

from sqlalchemy import func
from datetime import date, datetime

@app.get("/stats", response_class=HTMLResponse)
def stats_page(
    request: Request,
    db: Session = Depends(get_db),
    date_debut: str | None = None,
    date_fin: str | None = None
):
    # Définir la période
    if date_debut and date_fin:
        try:
            d1 = datetime.strptime(date_debut, "%Y-%m-%d").date()
            d2 = datetime.strptime(date_fin, "%Y-%m-%d").date()
        except ValueError:
            return HTMLResponse(content="<h1>Format de date invalide (YYYY-MM-DD)</h1>", status_code=400)
    else:
        year = date.today().year
        d1 = date(year, 1, 1)
        d2 = date(year, 12, 31)

    # Inspections filtrées par période
    inspections_count = db.query(models.Inspection)\
        .filter(models.Inspection.date.between(d1, d2)).count()

    # Navires
    navires_total = db.query(models.Navire).count()
    navires_a_quai = db.query(models.Navire)\
        .filter(models.Navire.statut_actuel == "à quai").count()

    # Audits par inspecteur
    audits_par_inspecteur = db.query(
        models.Inspection.inspecteur,
        func.count(models.Inspection.id)
    ).group_by(models.Inspection.inspecteur).all()

    # Global (année/période en cours) = inspections + navires
    global_total = inspections_count + navires_total

    return templates.TemplateResponse("stats.html", {
        "request": request,
        "periode": f"{d1} → {d2}",
        "inspections": inspections_count,
        "navires_total": navires_total,
        "navires_a_quai": navires_a_quai,
        "audits_par_inspecteur": audits_par_inspecteur,
        "global_total": global_total
    })


@app.get("/stats/download/{stat_type}")
def download_stats(
    stat_type: str,
    db: Session = Depends(get_db),
    date_debut: str | None = None,
    date_fin: str | None = None
):
    # Période
    if date_debut and date_fin:
        try:
            d1 = datetime.strptime(date_debut, "%Y-%m-%d").date()
            d2 = datetime.strptime(date_fin, "%Y-%m-%d").date()
        except ValueError:
            return HTMLResponse(content="<h1>Format de date invalide (YYYY-MM-DD)</h1>", status_code=400)
    else:
        year = date.today().year
        d1 = date(year, 1, 1)
        d2 = date(year, 12, 31)

    # Générer les données selon le type demandé
    if stat_type == "inspections":
        count = db.query(models.Inspection)\
            .filter(models.Inspection.date.between(d1, d2)).count()
        data = [
            ["Période", f"{d1} → {d2}"],
            ["Nombre d’inspections", count]
        ]

    elif stat_type == "navires":
        total = db.query(models.Navire).count()
        a_quai = db.query(models.Navire)\
            .filter(models.Navire.statut_actuel == "à quai").count()
        data = [
            ["Total navires", total],
            ["Navires à quai", a_quai]
        ]

    elif stat_type == "audits":
        audits = db.query(
            models.Inspection.inspecteur,
            func.count(models.Inspection.id)
        ).group_by(models.Inspection.inspecteur).all()
        data = [["Inspecteur", "Nombre d’audits"]] + [[i or "N/A", c] for i, c in audits]

    elif stat_type == "global":
        inspections_count = db.query(models.Inspection)\
            .filter(models.Inspection.date.between(d1, d2)).count()
        navires_total = db.query(models.Navire).count()
        global_total = inspections_count + navires_total
        data = [
            ["Période", f"{d1} → {d2}"],
            ["Chiffre global (inspections + navires)", global_total]
        ]

    else:
        return HTMLResponse(content="<h1>Statistique inconnue</h1>", status_code=404)

    # Génération du PDF
    file_path = f"stats_{stat_type}.pdf"
    build_pdf(file_path, f"MarineGab — Statistiques {stat_type}", data)
    return FileResponse(path=file_path, filename=file_path, media_type="application/pdf")

# -------------------------
# DECLARATIONS
# -------------------------

@app.get("/declarations", response_class=HTMLResponse)
def declarations_page(request: Request):
    return templates.TemplateResponse("declarations.html", {"request": request})

# --- Déclaration d’arrivée ---
@app.get("/declarations/arrivee", response_class=HTMLResponse)
def declaration_arrivee_form(request: Request, db: Session = Depends(get_db)):
    navires = db.query(models.Navire).all()
    return templates.TemplateResponse(
        "declaration_arrivee.html",
        {"request": request, "navires": navires}
    )

# ➜ Récupération des marchandises par navire_id
@app.get("/declarations/marchandises/by-id/{navire_id}", response_class=HTMLResponse)
def get_marchandises_by_navire_id(navire_id: int, db: Session = Depends(get_db)):
    marchandises = db.query(models.Marchandise).filter(models.Marchandise.navire_id == navire_id).all()
    if not marchandises:
        return HTMLResponse("<ul class='list'><li>Aucune marchandise enregistrée pour ce navire.</li></ul>")
    html = "".join([f"<li>{m.nom} — {m.poids} t</li>" for m in marchandises])
    return HTMLResponse(f"<ul class='list'>{html}</ul>")

# ➜ Récupération des marchandises par IMO
@app.get("/declarations/marchandises/{imo}", response_class=HTMLResponse)
def get_marchandises_by_navire(imo: str, db: Session = Depends(get_db)):
    navire = db.query(models.Navire).filter(models.Navire.imo == imo).first()
    if not navire:
        return HTMLResponse("<p class='error'>Navire introuvable pour cet IMO.</p>", status_code=404)

    marchandises = db.query(models.Marchandise).filter(models.Marchandise.navire_id == navire.id).all()
    if not marchandises:
        return HTMLResponse("<ul class='list'><li>Aucune marchandise enregistrée pour ce navire.</li></ul>")

    html = "".join([
        f"<li>{m.nom} — poids: {m.poids} t, volume: {m.volume} m³, tracking: {m.tracking_number}</li>"
        for m in marchandises
    ])
    return HTMLResponse(f"<ul class='list'>{html}</ul>")

@app.post("/declarations/arrivee/download")
def declaration_arrivee_download(
    navire_imo: str = Form(...),
    port: str = Form(...),
    date: str = Form(...),   # reçu comme string
    marchandises: str = Form(None),
    db: Session = Depends(get_db)
):
    # 🔹 Conversion de la chaîne en objet date
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return HTMLResponse("<h3>Format de date invalide (YYYY-MM-DD)</h3>", status_code=400)

    navire = db.query(models.Navire).filter(models.Navire.imo == navire_imo).first()
    marchandises_list = db.query(models.Marchandise).filter(
        models.Marchandise.navire_id == (navire.id if navire else None)
    ).all()

    data = [["Champ", "Valeur"]]
    data.append(["Nom du navire", navire.nom if navire else navire_imo])
    data.append(["Port d’arrivée", port])
    data.append(["Date d’arrivée", date_obj.strftime("%Y-%m-%d")])

    marchandises_text = None
    if marchandises_list:
        marchandises_text = "; ".join([f"{m.nom} ({m.poids}t)" for m in marchandises_list])
        for m in marchandises_list:
            data.append([f"Marchandise ({m.tracking_number})", f"{m.nom} — {m.poids}t / {m.volume}m³"])
    elif marchandises:
        marchandises_text = marchandises
        data.append(["Marchandises (manuel)", marchandises])

    filename = f"declaration_arrivee_{uuid.uuid4().hex}.pdf"
    file_path = os.path.join("app", "static", filename)
    build_pdf(file_path, "Déclaration d’arrivée", data)

    # 🔹 Utiliser date_obj (objet Python) et non la chaîne
    decl = models.Declaration(
        type="Arrivée",
        navire_nom=navire.nom if navire else navire_imo,
        navire_imo=navire_imo,
        port=port,
        date=date_obj,   # ✅ objet date
        marchandises=marchandises_text,
        fichier_pdf=filename
    )
    db.add(decl)
    db.commit()

    return FileResponse(file_path, filename=filename, media_type="application/pdf")

from datetime import datetime

@app.post("/declarations/depart/download")
def autorisation_depart_download(
    navire_imo: str = Form(...),
    port: str = Form(...),
    date: str = Form(...),   # reçu comme string
    destination: str = Form(None),
    securite: str = Form(...),
    sante: str = Form(None),
    db: Session = Depends(get_db)
):
    # 🔹 Conversion de la chaîne en objet date
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return HTMLResponse("<h3>Format de date invalide (YYYY-MM-DD)</h3>", status_code=400)

    navire = db.query(models.Navire).filter(models.Navire.imo == navire_imo).first()

    data = [["Champ", "Valeur"]]
    data.append(["Nom du navire", navire.nom if navire else navire_imo])
    data.append(["Port de départ", port])
    data.append(["Date de départ", date_obj.strftime("%Y-%m-%d")])
    if destination:
        data.append(["Destination", destination])
    data.append(["Niveau de sécurité", securite])
    if sante:
        data.append(["Déclaration de santé", sante])

    filename = f"autorisation_depart_{uuid.uuid4().hex}.pdf"
    file_path = os.path.join("app", "static", filename)
    build_pdf(file_path, "Autorisation de départ", data)

    # 🔹 Utiliser date_obj (objet Python) et non la chaîne
    decl = models.Declaration(
        type="Départ",
        navire_nom=navire.nom if navire else navire_imo,
        navire_imo=navire_imo,
        port=port,
        date=date_obj,   # ✅ objet date
        destination=destination,
        securite=securite,
        sante=sante,
        fichier_pdf=filename
    )
    db.add(decl)
    db.commit()

    return FileResponse(file_path, filename=filename, media_type="application/pdf")

# --- Liste des déclarations ---
@app.get("/declarations/list", response_class=HTMLResponse)
def declarations_list(request: Request, db: Session = Depends(get_db)):
    declarations = db.query(models.Declaration).all()
    return templates.TemplateResponse(
        "declarations_list.html",
        {"request": request, "declarations": declarations}
    )

# --- Autorisation de départ ---
@app.get("/declarations/depart", response_class=HTMLResponse)
def autorisation_depart_form(request: Request, db: Session = Depends(get_db)):
    navires = db.query(models.Navire).all()
    return templates.TemplateResponse(
        "autorisation_depart.html",
        {"request": request, "navires": navires}
    )

@app.post("/declarations/depart/download")
def autorisation_depart_download(
    navire_imo: str = Form(...),
    port: str = Form(...),
    date: str = Form(...),
    destination: str = Form(None),
    securite: str = Form(...),
    sante: str = Form(None),
    db: Session = Depends(get_db)
):
    navire = db.query(models.Navire).filter(models.Navire.imo == navire_imo).first()

    data = [["Champ", "Valeur"]]
    data.append(["Nom du navire", navire.nom if navire else navire_imo])
    data.append(["Port de départ", port])
    data.append(["Date de départ", date])
    if destination:
        data.append(["Destination", destination])
    data.append(["Niveau de sécurité", securite])
    if sante:
        data.append(["Déclaration de santé", sante])

    filename = f"autorisation_depart_{uuid.uuid4().hex}.pdf"
    file_path = os.path.join("app", "static", filename)
    build_pdf(file_path, "Autorisation de départ", data)

    # ➜ Insertion en base
    decl = models.Declaration(
        type="Départ",
        navire_nom=navire.nom if navire else navire_imo,
        navire_imo=navire_imo,
        port=port,
        date=date,
        destination=destination,
        securite=securite,
        sante=sante,
        fichier_pdf=filename
    )
    db.add(decl)
    db.commit()

    return FileResponse(file_path, filename=filename, media_type="application/pdf")

# --- Liste des déclarations ---
@app.get("/declarations/list", response_class=HTMLResponse)
def declarations_list(request: Request, db: Session = Depends(get_db)):
    declarations = db.query(models.Declaration).all()
    return templates.TemplateResponse(
        "declarations_list.html",
        {"request": request, "declarations": declarations}
    )

