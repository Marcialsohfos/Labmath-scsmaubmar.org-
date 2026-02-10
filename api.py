# api.py - À placer dans le site principal (labmath-scsmaubmar)
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
from datetime import datetime
from functools import wraps

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuration
API_KEY = os.environ.get('API_KEY', 'labmath_api_secret_2024')
DATA_FILE = 'data/data.json'

# Créer le dossier data s'il n'existe pas
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

# Décorateur pour vérifier l'API key
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({'success': False, 'message': 'API key invalide'}), 401
    return decorated_function

# Fonctions pour gérer le fichier JSON
def load_data():
    """Charge les données depuis le fichier JSON"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Retourne une structure vide si le fichier n'existe pas
        return {
            'activites': [],
            'realisations': [],
            'annonces': [],
            'offres': [],
            'last_update': datetime.now().isoformat()
        }

def save_data(data):
    """Sauvegarde les données dans le fichier JSON"""
    data['last_update'] = datetime.now().isoformat()
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Endpoints API
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'labmath-website',
        'timestamp': datetime.now().isoformat(),
        'data_file': os.path.exists(DATA_FILE)
    })

# --- GESTION DES ACTIVITÉS ---
@app.route('/api/activites', methods=['GET'])
def get_activites():
    """Récupère toutes les activités (public)"""
    db = load_data()
    # Retourne seulement les activités publiées
    activites_publiees = [a for a in db.get('activites', []) if a.get('est_publie', True)]
    return jsonify({'success': True, 'data': activites_publiees})

@app.route('/api/activites', methods=['POST'])
@app.route('/api/activites/<sync_id>', methods=['POST'])
@require_api_key
def manage_activite(sync_id=None):
    """Crée ou met à jour une activité (admin seulement)"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Données manquantes'}), 400
    
    db = load_data()
    
    # Utiliser l'ID de synchronisation de l'admin ou générer un nouveau
    item_id = sync_id or data.get('id')
    
    # Préparer l'activité
    activite = {
        'sync_id': str(item_id),
        'titre': data.get('titre', ''),
        'description': data.get('description', ''),
        'contenu': data.get('contenu', ''),
        'image_url': data.get('image_url', ''),
        'auteur': data.get('auteur', 'Admin'),
        'date_creation': data.get('date_creation', datetime.now().isoformat()),
        'date_modification': datetime.now().isoformat(),
        'est_publie': data.get('est_publie', True)
    }
    
    # Chercher si l'activité existe déjà
    found = False
    for i, item in enumerate(db.get('activites', [])):
        if str(item.get('sync_id')) == str(item_id):
            db['activites'][i] = activite
            found = True
            break
    
    # Sinon, ajouter comme nouvelle
    if not found:
        if 'activites' not in db:
            db['activites'] = []
        db['activites'].append(activite)
    
    save_data(db)
    return jsonify({'success': True, 'id': item_id, 'message': 'Activité sauvegardée'})

@app.route('/api/activites/<sync_id>', methods=['DELETE'])
@require_api_key
def delete_activite(sync_id):
    """Supprime une activité (admin seulement)"""
    db = load_data()
    
    # Filtrer pour supprimer l'activité avec le sync_id correspondant
    db['activites'] = [a for a in db.get('activites', []) 
                      if str(a.get('sync_id')) != str(sync_id)]
    
    save_data(db)
    return jsonify({'success': True, 'message': 'Activité supprimée'})

# --- GESTION DES RÉALISATIONS (similaire aux activités) ---
@app.route('/api/realisations', methods=['GET'])
def get_realisations():
    db = load_data()
    return jsonify({'success': True, 'data': db.get('realisations', [])})

@app.route('/api/realisations', methods=['POST'])
@app.route('/api/realisations/<sync_id>', methods=['POST'])
@require_api_key
def manage_realisation(sync_id=None):
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Données manquantes'}), 400
    
    db = load_data()
    item_id = sync_id or data.get('id')
    
    realisation = {
        'sync_id': str(item_id),
        'titre': data.get('titre', ''),
        'description': data.get('description', ''),
        'image_url': data.get('image_url', ''),
        'categorie': data.get('categorie', ''),
        'date_realisation': data.get('date_realisation'),
        'date_creation': data.get('date_creation', datetime.now().isoformat())
    }
    
    found = False
    for i, item in enumerate(db.get('realisations', [])):
        if str(item.get('sync_id')) == str(item_id):
            db['realisations'][i] = realisation
            found = True
            break
    
    if not found:
        if 'realisations' not in db:
            db['realisations'] = []
        db['realisations'].append(realisation)
    
    save_data(db)
    return jsonify({'success': True, 'id': item_id, 'message': 'Réalisation sauvegardée'})

@app.route('/api/realisations/<sync_id>', methods=['DELETE'])
@require_api_key
def delete_realisation(sync_id):
    db = load_data()
    db['realisations'] = [r for r in db.get('realisations', []) 
                         if str(r.get('sync_id')) != str(sync_id)]
    save_data(db)
    return jsonify({'success': True, 'message': 'Réalisation supprimée'})

# --- GESTION DES ANNONCES (similaire) ---
@app.route('/api/annonces', methods=['GET'])
def get_annonces():
    db = load_data()
    # Retourne seulement les annonces actives
    annonces_actives = [a for a in db.get('annonces', []) if a.get('est_active', True)]
    return jsonify({'success': True, 'data': annonces_actives})

@app.route('/api/annonces', methods=['POST'])
@app.route('/api/annonces/<sync_id>', methods=['POST'])
@require_api_key
def manage_annonce(sync_id=None):
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Données manquantes'}), 400
    
    db = load_data()
    item_id = sync_id or data.get('id')
    
    annonce = {
        'sync_id': str(item_id),
        'titre': data.get('titre', ''),
        'contenu': data.get('contenu', ''),
        'type_annonce': data.get('type_annonce', 'info'),
        'date_debut': data.get('date_debut'),
        'date_fin': data.get('date_fin'),
        'date_creation': data.get('date_creation', datetime.now().isoformat()),
        'est_active': data.get('est_active', True)
    }
    
    found = False
    for i, item in enumerate(db.get('annonces', [])):
        if str(item.get('sync_id')) == str(item_id):
            db['annonces'][i] = annonce
            found = True
            break
    
    if not found:
        if 'annonces' not in db:
            db['annonces'] = []
        db['annonces'].append(annonce)
    
    save_data(db)
    return jsonify({'success': True, 'id': item_id, 'message': 'Annonce sauvegardée'})

@app.route('/api/annonces/<sync_id>', methods=['DELETE'])
@require_api_key
def delete_annonce(sync_id):
    db = load_data()
    db['annonces'] = [a for a in db.get('annonces', []) 
                     if str(a.get('sync_id')) != str(sync_id)]
    save_data(db)
    return jsonify({'success': True, 'message': 'Annonce supprimée'})

# --- GESTION DES OFFRES (similaire) ---
@app.route('/api/offres', methods=['GET'])
def get_offres():
    db = load_data()
    offres_actives = [o for o in db.get('offres', []) if o.get('est_active', True)]
    return jsonify({'success': True, 'data': offres_actives})

@app.route('/api/offres', methods=['POST'])
@app.route('/api/offres/<sync_id>', methods=['POST'])
@require_api_key
def manage_offre(sync_id=None):
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Données manquantes'}), 400
    
    db = load_data()
    item_id = sync_id or data.get('id')
    
    offre = {
        'sync_id': str(item_id),
        'titre': data.get('titre', ''),
        'description': data.get('description', ''),
        'type_offre': data.get('type_offre', 'autre'),
        'lieu': data.get('lieu', ''),
        'date_limite': data.get('date_limite'),
        'date_creation': data.get('date_creation', datetime.now().isoformat()),
        'est_active': data.get('est_active', True)
    }
    
    found = False
    for i, item in enumerate(db.get('offres', [])):
        if str(item.get('sync_id')) == str(item_id):
            db['offres'][i] = offre
            found = True
            break
    
    if not found:
        if 'offres' not in db:
            db['offres'] = []
        db['offres'].append(offre)
    
    save_data(db)
    return jsonify({'success': True, 'id': item_id, 'message': 'Offre sauvegardée'})

@app.route('/api/offres/<sync_id>', methods=['DELETE'])
@require_api_key
def delete_offre(sync_id):
    db = load_data()
    db['offres'] = [o for o in db.get('offres', []) 
                   if str(o.get('sync_id')) != str(sync_id)]
    save_data(db)
    return jsonify({'success': True, 'message': 'Offre supprimée'})

# --- ROUTES POUR LE SITE WEB ---
@app.route('/')
def index():
    """Route principale du site"""
    return render_template('index.html')

@app.route('/activites')
def activites_page():
    """Page des activités"""
    return render_template('activites.html')

@app.route('/realisations')
def realisations_page():
    """Page des réalisations"""
    return render_template('realisations.html')

@app.route('/annonces')
def annonces_page():
    """Page des annonces"""
    return render_template('annonces.html')

@app.route('/offres')
def offres_page():
    """Page des offres"""
    return render_template('offres.html')

# --- EXÉCUTION ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)