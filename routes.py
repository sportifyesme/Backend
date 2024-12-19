from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import SessionLocal
from models import User, Match, Event, Participant, Stat
import matplotlib.pyplot as plt  # Pour dessiner des graphiques
import io  # Pour gérer les entrées/sorties en mémoire
import base64
from pyfcm import FCMNotification
import requests

router = Blueprint('router', __name__)


#API d'inscription : Inscription d'un utilisateur -> fragment_register
@router.route("/api/register", methods=["POST"])
def register_user():
    user_data = request.json
    db: Session = SessionLocal()

    sports_valides = ["Football", "Tennis", "Basketball", "Natation"]
    niveaux_valides = ["Débutant", "Intermédiaire", "Avancé"]

    # Validation des champs
    if user_data.get("sport") not in sports_valides:
        return jsonify({
            "error": f"Le sport doit être parmi : {', '.join(sports_valides)}",
            "sports": sports_valides,
            "niveaux": niveaux_valides
        }), 400

    if user_data.get("niveau") not in niveaux_valides:
        return jsonify({
            "error": f"Le niveau doit être parmi : {', '.join(niveaux_valides)}",
            "sports": sports_valides,
            "niveaux": niveaux_valides
        }), 400

    try:
        # Création de l'utilisateur
        new_user = User(
            nom_utilisateur=user_data["nom_utilisateur"],
            email=user_data["email"],
            mot_de_passe=user_data["mot_de_passe"],
            sport=user_data["sport"],
            niveau=user_data["niveau"]
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return jsonify({
            "success": True,
            "message": "Utilisateur créé avec succès",
            "user_id": new_user.id
        }), 201

    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Cet email est déjà utilisé"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

#API de connexion : Connexion d'un utilisateur -> fragment_login
@router.route("/api/login", methods=["POST"])
def login_user():
    user_data = request.json
    db: Session = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == user_data['email'], 
                                      User.mot_de_passe == user_data['mot_de_passe']).first()
        if user:
            return jsonify({"message": "Login successful", "user_id": user.id}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


#API de Récupération des Utilisateurs -> fragment_home
@router.route("/api/users", methods=["GET"])
def get_users():
    db: Session = SessionLocal()
    try:
        users = db.query(User).all()  # Récupérer tous les utilisateurs
        return jsonify([{
            "id": user.id,
            "nom_utilisateur": user.nom_utilisateur,
            "email": user.email,
            "sport": user.sport,
            "niveau": user.niveau
        } for user in users])  # Renvoie les données au format JSON
    except Exception as e:
        return jsonify({"error": "Failed to fetch users", "details": str(e)}), 400
    finally:
        db.close()


#API de Profil utilisateur -> fragment_home
@router.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return jsonify({
                "id": user.id,
                "nom_utilisateur": user.nom_utilisateur,
                "email": user.email,
                "sport": user.sport,
                "niveau": user.niveau
            }), 200
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": "Failed to fetch user", "details": str(e)}), 400
    finally:
        db.close()


#Mise à Jour des Données Utilisateur -> fragment_home
@router.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user_data = request.json
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            return jsonify({"error": "User not found"}), 404
        
        user.nom_utilisateur = user_data.get('nom_utilisateur', user.nom_utilisateur)
        user.email = user_data.get('email', user.email)
        user.sport = user_data.get('sport', user.sport)
        user.niveau = user_data.get('niveau', user.niveau)

        db.commit()
        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": "Failed to update user", "details": str(e)}), 400
    finally:
        db.close()        


#API : créer un match -> activity_create_match
@router.route("/api/match/create", methods=["POST"])
def create_match():
    match_data = request.json
    db = SessionLocal()
    try:
        # Vérifiez que l'utilisateur organisateur existe
        organisateur = db.query(User).filter(User.id == match_data["id_organisateur"]).first()
        if not organisateur:
            return jsonify({"error": "Utilisateur introuvable"}), 404

        # Créez le match
        match = Match(
            titre=match_data["titre"],
            description=match_data["description"],
            date=match_data["date"],
            lieu=match_data["lieu"],
            niveau=match_data["niveau"],  # "Débutant", "Intermédiaire", ou "Avancé"
            max_participants=match_data["max_participants"],
            id_organisateur=match_data["id_organisateur"],
            sport=match_data["sport"]
        )
        db.add(match)
        db.commit()
        return jsonify({"message": "Match créé avec succès", "match_id": match.id}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


#API : rejoindre un match -> activity_join_match
@router.route("/api/match/join", methods=["POST"])
def join_match():
    join_data = request.json
    db = SessionLocal()

    # Validation des champs obligatoires
    required_fields = ["match_id", "user_id"]
    for field in required_fields:
        if not join_data.get(field):
            return jsonify({"error": f"Le champ '{field}' est requis"}), 400

    try:
        # Récupération du match
        match = db.query(Match).filter(Match.id == join_data["match_id"]).first()
        if not match:
            return jsonify({"error": "Match introuvable"}), 404

        # Vérifier si le match est complet
        current_participants = db.query(Participant).filter(Participant.match_id == match.id).count()
        if current_participants >= match.max_participants:
            return jsonify({"error": "Le match est complet"}), 400

        # Vérifier si l'utilisateur est déjà inscrit au match
        existing_participant = db.query(Participant).filter(
            Participant.match_id == join_data["match_id"],
            Participant.user_id == join_data["user_id"]
        ).first()
        if existing_participant:
            return jsonify({"error": "L'utilisateur est déjà inscrit à ce match"}), 400

        # Associer l'utilisateur au match
        new_participant = Participant(
            match_id=join_data["match_id"],
            user_id=join_data["user_id"]
        )
        db.add(new_participant)
        db.commit()

        return jsonify({"message": "Participation confirmée"}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Une erreur est survenue : {str(e)}"}), 500

    finally:
        db.close()


#API : récuperer les matchs -> activity_join_match
@router.route("/api/match/list", methods=["GET"])
def list_matches():
    db: Session = SessionLocal()
    try:
        matches = db.query(Match).all()
        return jsonify([{
            "id": match.id,
            "titre": match.titre,
            "description": match.description,
            "date": match.date,
            "lieu": match.lieu,
            "niveau": match.niveau,
            "sport":match.sport,
            "max_participants": match.max_participants,
            "id_organisateur": match.id_organisateur,
            "organisateur_nom": match.organisateur.nom_utilisateur
        } for match in matches]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


#API : récuperer les participants : MatchmakingAdapter
@router.route("/api/match/<int:match_id>/participants", methods=["GET"])
def get_match_participants(match_id):
    db: Session = SessionLocal()
    try:
        # Récupérer les participants avec les informations sur les utilisateurs
        participants = (
            db.query(Participant)
            .filter(Participant.match_id == match_id)
            .join(User, Participant.user_id == User.id)
            .join(Match, Participant.match_id == Match.id)  # Ajouter une jointure avec Match pour récupérer le sport
            .all()
        )

        # Construire la liste des participants avec leur ID, nom d'utilisateur et le sport du match
        response_data = [
            {
                "id": participant.user.id,  # ID utilisateur
                "nom_utilisateur": participant.user.nom_utilisateur,  # Nom d'utilisateur
                "sport": participant.match.sport  # Sport du match
            }
            for participant in participants
        ]

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": f"Une erreur est survenue : {str(e)}"}), 500
    finally:
        db.close()


#API : Ajouter les statistiques -> FragmentStats
@router.route("/api/stats", methods=["POST"])
def add_stat():
    data = request.json
    db: Session = SessionLocal()

    try:
        # Validation des données
        if not data.get("user_id") or not data.get("categorie") or not data.get("sport"):
            return jsonify({"error": "Les champs 'user_id', 'categorie', et 'sport' sont obligatoires."}), 400
        
        # Ajouter la statistique avec seulement les champs fournis
        new_stat = Stat(
            user_id=data["user_id"],
            categorie=data["categorie"],
            sport=data["sport"],
            buts=data.get("buts") or 0,  # Mettre à 0 si non fourni
            passes_decisives=data.get("passes_decisives") or 0,
            minutes_jouees=data.get("minutes_jouees") or 0,
            rebonds=data.get("rebonds") or 0,  # Pour le Basketball
            aces=data.get("aces") or 0,  # Pour le Tennis
            double_faults=data.get("double_faults") or 0,
            games_won=data.get("games_won") or 0,
            distance_swum=data.get("distance_swum") or 0,  # Pour la Natation
            strokes=data.get("strokes") or 0
        )
        
        db.add(new_stat)
        db.commit()
        db.refresh(new_stat)

        return jsonify({"message": "Statistique ajoutée avec succès.", "stat_id": new_stat.id}), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


#API statistique : Récupérer l'historique des statistiques -> FragmentStats
@router.route("/api/stats/history/<int:user_id>", methods=["GET"])
def get_stats_history(user_id):
    db: Session = SessionLocal()

    try:
        # Récupérer toutes les statistiques pour un utilisateur donné
        stats = db.query(Stat).filter(Stat.user_id == user_id).all()

        if not stats:
            return jsonify({"error": "Aucune statistique trouvée pour cet utilisateur."}), 404

        # Renvoie les statistiques avec dates, catégories, et d'autres informations
        response_data = []
        for stat in stats:
            stat_data = {
                "categorie": stat.categorie,
                "sport": stat.sport,
                "date": stat.date.strftime("%Y-%m-%d %H:%M:%S"),
            }
            # Inclure les champs pertinents pour chaque sport
            if stat.sport == "Football":
                stat_data.update({
                    "buts": stat.buts,
                    "passes_decisives": stat.passes_decisives,
                    "minutes_jouees": stat.minutes_jouees
                })
            elif stat.sport == "Basketball":
                stat_data.update({
                    "buts": stat.buts,
                    "passes_decisives": stat.passes_decisives,
                    "rebonds": stat.rebonds,
                    "minutes_jouees": stat.minutes_jouees
                })
            elif stat.sport == "Tennis":
                stat_data.update({
                    "aces": stat.aces,
                    "double_faults": stat.double_faults,
                    "games_won": stat.games_won,
                    "minutes_jouees": stat.minutes_jouees
                })
            elif stat.sport == "Natation":
                stat_data.update({
                    "distance_swum": stat.distance_swum,
                    "strokes": stat.strokes,
                    "minutes_jouees": stat.minutes_jouees
                })

            response_data.append(stat_data)
        
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()



    db: Session = SessionLocal()

    try:
        stats = db.query(Stat).filter(Stat.user_id == user_id).all()
        if not stats:
            return jsonify({"error": "Aucune statistique trouvée pour cet utilisateur."}), 404

        return jsonify([{"categorie": stat.categorie, "valeur": stat.valeur} for stat in stats]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        db.close()


    db: Session = SessionLocal()

    try:
        stats = db.query(Stat).filter(Stat.user_id == user_id).all()
        if not stats:
            return jsonify({"error": "Aucune statistique trouvée."}), 404

        return jsonify([{
            "categorie": stat.categorie,
            "valeur": stat.valeur,
            "sport": stat.sport,
            "date": stat.date.strftime("%Y-%m-%d %H:%M:%S")  # Format de la date
        } for stat in stats]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()



    db = SessionLocal()
    try:
        events = db.query(Event).all()
        return jsonify([{
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date
        } for event in events]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch events", "details": str(e)}), 500
    finally:
        db.close()


#API pour supprimer toutes les tables
@router.route("/api/admin/clear", methods=["DELETE"])
def clear_data():
    db: Session = SessionLocal()
    try:
        # Supprimer les participants
        db.query(Participant).delete()

        # Supprimer les matchs
        db.query(Match).delete()

        # Supprimer les utilisateurs
        db.query(User).delete()

        db.commit()
        return jsonify({"message": "Toutes les données ont été supprimées avec succès"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()
