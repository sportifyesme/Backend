from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Text
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

    # Relation avec les événements créés
    evenements = relationship("Event", back_populates="organisateur")
    activites = relationship("Activity", back_populates="utilisateur")


class Event(Base):
    __tablename__ = 'evenements'
    
    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(255), nullable=False)
    description = Column(Text)
    date = Column(DateTime, nullable=False)
    lieu = Column(String(255), nullable=False)
    id_organisateur = Column(Integer, ForeignKey('utilisateurs.id'))

    # Relation avec l'utilisateur
    organisateur = relationship("User", back_populates="evenements")


class Activity(Base):
    __tablename__ = 'activites'
    
    id = Column(Integer, primary_key=True, index=True)
    type_activite = Column(String(100))
    duree = Column(Integer)  # Durée en minutes
    date = Column(DateTime, nullable=False)
    id_utilisateur = Column(Integer, ForeignKey('utilisateurs.id'))

    # Relation avec l'utilisateur
    utilisateur = relationship("User", back_populates="activites")


class Matchmaking(Base):
    __tablename__ = 'matchmaking'
    
    id = Column(Integer, primary_key=True, index=True)
    id_utilisateur_1 = Column(Integer, ForeignKey('utilisateurs.id'))
    id_utilisateur_2 = Column(Integer, ForeignKey('utilisateurs.id'))
    date_creation = Column(DateTime, server_default='CURRENT_TIMESTAMP')

    # Relations pour les utilisateurs
    utilisateur_1 = relationship("User", foreign_keys=[id_utilisateur_1])
    utilisateur_2 = relationship("User", foreign_keys=[id_utilisateur_2])