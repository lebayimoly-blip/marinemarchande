from sqlalchemy import Column, Integer, String, Float, Date, Text
from app.database import Base


class Navire(Base):
    __tablename__ = "navires"

    id = Column(Integer, primary_key=True, index=True)
    imo = Column(String(50), unique=True, nullable=False)
    nom = Column(String(255), nullable=False)
    pavillon = Column(String(100), nullable=True)
    annee_construction = Column(Integer, nullable=True)
    tonnage = Column(Float, nullable=True)
    type = Column(String(100), nullable=True)

    # Champs supplémentaires
    dernier_port = Column(String(100), nullable=True)
    prochaine_destination = Column(String(100), nullable=True)
    statut_actuel = Column(String(100), nullable=True)
    autres = Column(Text, nullable=True)


class Port(Base):
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), unique=True, nullable=False)
    pays = Column(String(100), nullable=True)
    ville = Column(String(100), nullable=True)
    capacite = Column(Float, nullable=True)
    type = Column(String(100), nullable=True)
    coordonnees = Column(String(255), nullable=True)
    responsable = Column(String(255), nullable=True)


class Marchandise(Base):
    __tablename__ = "marchandises"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    type = Column(String(100), nullable=True)
    poids = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Référence au navire
    navire_id = Column(Integer, nullable=False)

    # Nouveau champ
    tracking_number = Column(String(100), unique=True, nullable=False)

class Manifest(Base):
    __tablename__ = "manifests"

    id = Column(Integer, primary_key=True, index=True)
    numero_manifest = Column(String(255), unique=True, nullable=False)
    date = Column(Date, nullable=False)
    navire_imo = Column(String(50), nullable=False)
    port_depart_nom = Column(String(100), nullable=False)
    port_arrivee_nom = Column(String(100), nullable=False)


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    navire_imo = Column(String(50), nullable=False)
    port_nom = Column(String(100), nullable=False)
    inspecteur = Column(String(255), nullable=False)
    rapport = Column(Text, nullable=True)

    # Nouveaux champs audit
    certificat_securite = Column(String(20), nullable=False, default="Non conforme")
    certificat_classe = Column(String(20), nullable=False, default="Non conforme")
    certificat_pollution = Column(String(20), nullable=False, default="Non conforme")

    brevets_marins = Column(String(20), nullable=False, default="Non conforme")
    certificats_medicaux = Column(String(20), nullable=False, default="Non conforme")
    journal_bord = Column(String(20), nullable=False, default="Non conforme")
    papiers_douaniers = Column(String(20), nullable=False, default="Non conforme")

    gilets_combinaisons = Column(String(20), nullable=False, default="Non conforme")
    radeaux_canots = Column(String(20), nullable=False, default="Non conforme")
    extincteurs = Column(String(20), nullable=False, default="Non conforme")
    alarmes_detecteurs = Column(String(20), nullable=False, default="Non conforme")
    systeme_incendie = Column(String(20), nullable=False, default="Non conforme")

    normes_antipollution = Column(String(20), nullable=False, default="Non conforme")
    conditions_vie = Column(String(20), nullable=False, default="Non conforme")

    observations = Column(Text, nullable=True)

from sqlalchemy import Column, Integer, String, Date
from app.database import Base

class Declaration(Base):
    __tablename__ = "declarations"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)          # "Arrivée" ou "Départ"
    navire_nom = Column(String, nullable=False)
    navire_imo = Column(String, nullable=False)
    port = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    destination = Column(String, nullable=True)
    marchandises = Column(String, nullable=True)
    securite = Column(String, nullable=True)
    sante = Column(String, nullable=True)
    fichier_pdf = Column(String, nullable=False)   # chemin du PDF généré
