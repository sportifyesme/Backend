from flask import Flask
from routes import router  # Assurez-vous que ce module est compatible avec Flask

app = Flask(__name__)

# Enregistrement des routes
app.register_blueprint(router)

@app.route("/", methods=["GET"])
def read_root():
    return {"message": "Welcome to Sportify API!"}

if __name__ == "__main__":
    app.run(debug=True)

    