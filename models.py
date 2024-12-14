from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Float, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = 'utilisateurs'

    id = Column(Integer, primary_key=True, index=True)
    nom_utilisateur = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    mot_de_passe = Column(String(255))
    sport = Column(String(100))
    niveau = Column(Enum('Débutant', 'Intermédiaire', 'Avancé'))
    date_inscription = Column(DateTime, server_default='CURRENT_TIMESTAMP')
    stats = relationship("Stat", back_populates="utilisateur")
    matchs = relationship("Match", back_populates="organisateur")

class Match(Base):
    __tablename__ = 'matchs'

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    lieu = Column(String(255), nullable=False)
    id_organisateur = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    niveau = Column(Enum('Débutant', 'Intermédiaire', 'Avancé'))  # Niveau requis
    max_participants = Column(Integer, nullable=False)  # Nombre maximum de participants
    participants = relationship("Participant", back_populates="match")
    organisateur = relationship("User", back_populates="matchs")

class Event(Base):
    __tablename__ = 'evenements'

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    lieu = Column(String(255), nullable=False)
    id_organisateur = Column(Integer, ForeignKey('utilisateurs.id'))
    is_admin_event = Column(Boolean, default=True)

class Participant(Base):
    __tablename__ = 'participants'

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey('matchs.id'))
    user_id = Column(Integer, ForeignKey('utilisateurs.id'))
    match = relationship("Match", back_populates="participants")

class Stat(Base):
    __tablename__ = 'statistiques'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('utilisateurs.id'))
    categorie = Column(String(255))
    valeur = Column(Float)
    date = Column(DateTime, server_default='CURRENT_TIMESTAMP')
    utilisateur = relationship("User", back_populates="stats")
