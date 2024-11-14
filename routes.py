from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

router = Blueprint('router', __name__)

@router.route("/api/register", methods=["POST"])
def register_user():
    user_data = request.json
    
    # Starting a new session
    db: Session = SessionLocal()
    
    try:
        # Create a new User instance
        user = User(**user_data)
        print("User registered data:", user_data)
        
        # Add the user to the session and commit
        db.add(user)
        db.commit()
        
        # Refresh the user instance to get the new ID
        db.refresh(user)

        return jsonify({"message": "User registered successfully", "user_id": user.id}), 201
    
    except Exception as e:
        db.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 400
    
    finally:
        db.close()  # Close the session

        