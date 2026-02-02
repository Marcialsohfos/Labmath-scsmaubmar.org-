#!/usr/bin/env python3
"""
Backend pour le formulaire de contact Lab_Math
À déployer sur Render avec PostgreSQL
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
CORS(app)  # Activer CORS pour les requêtes frontend

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = os.environ.get('EMAIL_PORT', 587)
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'contact@labmath.com')

def init_db():
    """Initialiser la base de données"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Créer la table des contacts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            subject VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending'
        )
    ''')
    
    # Créer la table des logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_logs (
            id SERIAL PRIMARY KEY,
            contact_id INTEGER REFERENCES contacts(id),
            action VARCHAR(50),
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

def send_email(to_email, subject, body):
    """Envoyer un email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Erreur d'envoi d'email: {e}")
        return False

@app.route('/')
def home():
    """Page d'accueil de l'API"""
    return jsonify({
        'message': 'Lab_Math Contact API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/contact': 'Soumettre un formulaire de contact',
            'GET /api/health': 'Vérifier l\'état de l\'API'
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Vérifier l'état de l'API"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    """Traiter le formulaire de contact"""
    try:
        data = request.json
        
        # Validation des données
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({
                    'success': False,
                    'error': f'Le champ {field} est requis'
                }), 400
        
        # Validation de l'email
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, data['email']):
            return jsonify({
                'success': False,
                'error': 'Adresse email invalide'
            }), 400
        
        # Connexion à la base de données
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Insérer le contact
        cursor.execute('''
            INSERT INTO contacts (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (data['name'], data['email'], data['subject'], data['message']))
        
        contact_id = cursor.fetchone()[0]
        
        # Logger l'action
        cursor.execute('''
            INSERT INTO contact_logs (contact_id, action, details)
            VALUES (%s, %s, %s)
        ''', (contact_id, 'submitted', json.dumps(data)))
        
        conn.commit()
        
        # Envoyer les emails
        # 1. Email de confirmation à l'utilisateur
        user_email_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #0a192f; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Lab_Math</h1>
                    <p>Confirmation de réception</p>
                </div>
                <div class="content">
                    <h2>Bonjour {data['name']},</h2>
                    <p>Nous avons bien reçu votre message et nous vous en remercions.</p>
                    <p><strong>Sujet :</strong> {data['subject']}</p>
                    <p><strong>Votre message :</strong></p>
                    <p>{data['message']}</p>
                    <p>Notre équipe va examiner votre demande et vous répondra dans les plus brefs délais (généralement sous 24 heures ouvrables).</p>
                    <p>Cordialement,<br>L'équipe Lab_Math</p>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} Lab_Math. Tous droits réservés.</p>
                    <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 2. Email de notification à l'admin
        admin_email_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #0a192f; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .info-box {{ background: #e3f2fd; padding: 15px; border-left: 4px solid #00bcd4; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Nouveau contact Lab_Math</h1>
                </div>
                <div class="content">
                    <div class="info-box">
                        <p><strong>De :</strong> {data['name']} ({data['email']})</p>
                        <p><strong>Sujet :</strong> {data['subject']}</p>
                        <p><strong>Date :</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                        <p><strong>ID :</strong> {contact_id}</p>
                    </div>
                    <h3>Message :</h3>
                    <p>{data['message']}</p>
                    <p><a href="{request.host_url}admin/contacts/{contact_id}">Voir dans l'admin</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Envoyer les emails (dans un environnement de production)
        if os.environ.get('ENVIRONMENT') == 'production':
            send_email(data['email'], 'Confirmation de réception - Lab_Math', user_email_body)
            send_email(ADMIN_EMAIL, f'Nouveau contact: {data["subject"]}', admin_email_body)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Message envoyé avec succès',
            'contact_id': contact_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur interne: {str(e)}'
        }), 500

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Récupérer la liste des contacts (pour l'admin)"""
    # Vérifier l'authentification (basique pour l'exemple)
    auth = request.headers.get('Authorization')
    if auth != f'Bearer {os.environ.get("ADMIN_TOKEN")}':
        return jsonify({'error': 'Non autorisé'}), 401
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, subject, message, created_at, status
            FROM contacts
            ORDER BY created_at DESC
            LIMIT 100
        ''')
        
        columns = [desc[0] for desc in cursor.description]
        contacts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'contacts': contacts,
            'count': len(contacts)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialiser la base de données
    init_db()
    
    # Démarrer le serveur
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG') == 'True')