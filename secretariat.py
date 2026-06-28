import sqlite3
import os
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
DB_NAME = "secretariat.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL, email TEXT, telephone TEXT, entreprise TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courriers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL, expediteur TEXT NOT NULL, 
                destinataire TEXT NOT NULL, objet TEXT NOT NULL, date_reception TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS taches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL, description TEXT, statut TEXT DEFAULT 'En attente'
            )
        ''')
        conn.commit()

# --- TEMPLATES HTML (Intégrés pour simplifier le script unique) ---
BASE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Secrétariat Pro</title>
    <link rel="stylesheet" href="https://jsdelivr.net">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">📁 Secrétariat Central</a>
            <div class="navbar-nav">
                <a class="nav-link text-white" href="/contacts">👥 Contacts</a>
                <a class="nav-link text-white" href="/courriers">✉️ Courriers</a>
                <a class="nav-link text-white" href="/taches">📋 Tâches</a>
            </div>
        </div>
    </nav>
    <div class="container">{% block content %}{% endblock %}</div>
</body>
</html>
"""

INDEX_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<div class="row text-center">
    <h2 class="mb-4">Tableau de Bord du Secrétariat</h2>
    <div class="col-md-4"><div class="card p-4 shadow-sm"><h3>👥 Contacts</h3><a href="/contacts" class="btn btn-primary mt-2">Gérer</a></div></div>
    <div class="col-md-4"><div class="card p-4 shadow-sm"><h3>✉️ Courriers</h3><a href="/courriers" class="btn btn-warning mt-2">Suivre</a></div></div>
    <div class="col-md-4"><div class="card p-4 shadow-sm"><h3>📋 Tâches</h3><a href="/taches" class="btn btn-success mt-2">Consulter</a></div></div>
</div>
""")

CONTACTS_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<h2>👥 Gestion des Contacts</h2>
<div class="card p-3 my-3">
    <h5>Ajouter un contact</h5>
    <form action="/contacts/ajouter" method="POST" class="row g-2">
        <div class="col"><input type="text" name="nom" class="form-control" placeholder="Nom complet" required></div>
        <div class="col"><input type="email" name="email" class="form-control" placeholder="Email"></div>
        <div class="col"><input type="text" name="telephone" class="form-control" placeholder="Téléphone"></div>
        <div class="col"><input type="text" name="entreprise" class="form-control" placeholder="Entreprise"></div>
        <div class="col-auto"><button type="submit" class="btn btn-primary">Ajouter</button></div>
    </form>
</div>
<table class="table table-striped table-hover bg-white shadow-sm">
    <thead class="table-dark"><tr><th>Nom</th><th>Email</th><th>Téléphone</th><th>Entreprise</th></tr></thead>
    <tbody>
        {% for c in contacts %}
        <tr><td>{{c[1]}}</td><td>{{c[2]}}</td><td>{{c[3]}}</td><td>{{c[4]}}</td></tr>
        {% endfor %}
    </tbody>
</table>
""")

COURRIERS_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<h2>✉️ Suivi du Courrier</h2>
<div class="card p-3 my-3">
    <h5>Enregistrer un courrier</h5>
    <form action="/courriers/ajouter" method="POST" class="row g-2">
        <div class="col"><select name="type" class="form-select"><option>Arrivée</option><option>Départ</option></select></div>
        <div class="col"><input type="text" name="expediteur" class="form-control" placeholder="Expéditeur" required></div>
        <div class="col"><input type="text" name="destinataire" class="form-control" placeholder="Destinataire" required></div>
        <div class="col"><input type="text" name="objet" class="form-control" placeholder="Objet" required></div>
        <div class="col"><input type="date" name="date" class="form-control" required></div>
        <div class="col-auto"><button type="submit" class="btn btn-warning">Enregistrer</button></div>
    </form>
</div>
<table class="table table-striped table-hover bg-white shadow-sm">
    <thead class="table-dark"><tr><th>Type</th><th>Expéditeur</th><th>Destinataire</th><th>Objet</th><th>Date</th></tr></thead>
    <tbody>
        {% for cr in courriers %}
        <tr>
            <td><span class="badge {% if cr[1]=='Arrivée' %}bg-info{% else %}bg-secondary{% endif %}">{{cr[1]}}</span></td>
            <td>{{cr[2]}}</td><td>{{cr[3]}}</td><td>{{cr[4]}}</td><td>{{cr[5]}}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
""")

TACHES_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
<h2>📋 Liste des Tâches</h2>
<div class="card p-3 my-3">
    <h5>Créer une tâche</h5>
    <form action="/taches/ajouter" method="POST" class="row g-2">
        <div class="col-md-4"><input type="text" name="titre" class="form-control" placeholder="Titre de la tâche" required></div>
        <div class="col-md-6"><input type="text" name="desc" class="form-control" placeholder="Description"></div>
        <div class="col-md-2"><button type="submit" class="btn btn-success w-100">Créer</button></div>
    </form>
</div>
<div class="row">
    {% for t in taches %}
    <div class="col-md-4 mb-3">
        <div class="card shadow-sm">
            <div class="card-body">
                <h5 class="card-title">{{t[1]}}</h5>
                <p class="card-text text-muted">{{t[2]}}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <span class="badge bg-warning text-dark">{{t[3]}}</span>
                    {% if t[3] != 'Terminé' %}
                    <a href="/taches/terminer/{{t[0]}}" class="btn btn-sm btn-outline-success">Terminer</a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
""")

# --- ROUTES DE L'APPLICATION ---
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/contacts')
def list_contacts():
    with sqlite3.connect(DB_NAME) as conn:
        contacts = conn.execute("SELECT * FROM contacts ORDER BY nom ASC").fetchall()
    return render_template_string(CONTACTS_HTML, contacts=contacts)

@app.route('/contacts/ajouter', methods=['POST'])
def ajouter_contact():
    nom, email, tel, entreprise = request.form['nom'], request.form['email'], request.form['telephone'], request.form['entreprise']
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO contacts (nom, email, telephone, entreprise) VALUES (?, ?, ?, ?)", (nom, email, tel, entreprise))
    return redirect(url_for('list_contacts'))

@app.route('/courriers')
def list_courriers():
    with sqlite3.connect(DB_NAME) as conn:
        courriers = conn.execute("SELECT * FROM courriers ORDER BY date_reception DESC").fetchall()
    return render_template_string(COURRIERS_HTML, courriers=courriers)

@app.route('/courriers/ajouter', methods=['POST'])
def ajouter_courrier():
    t, exp, dest, obj, dt = request.form['type'], request.form['expediteur'], request.form['destinataire'], request.form['objet'], request.form['date']
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO courriers (type, expediteur, destinataire, objet, date_reception) VALUES (?, ?, ?, ?, ?)", (t, exp, dest, obj, dt))
    return redirect(url_for('list_courriers'))

@app.route('/taches')
def list_taches():
    with sqlite3.connect(DB_NAME) as conn:
        taches = conn.execute("SELECT * FROM taches ORDER BY id DESC").fetchall()
    return render_template_string(TACHES_HTML, taches=taches)

@app.route('/taches/ajouter', methods=['POST'])
def ajouter_tache():
    titre, desc = request.form['titre'], request.form['desc']
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO taches (titre, description) VALUES (?, ?)", (titre, desc))
    return redirect(url_for('list_taches'))

@app.route('/taches/terminer/<int:tache_id>')
def terminer_tache(tache_id):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE taches SET statut='Terminé' WHERE id=?", (tache_id,))
    return redirect(url_for('list_taches'))

if __name__ == '__main__':
    init_db()
    # Récupère le port du serveur distant ou utilise 5000 par défaut
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
