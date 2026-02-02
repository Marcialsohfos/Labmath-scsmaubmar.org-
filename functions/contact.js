// Netlify Function pour traiter le formulaire de contact
exports.handler = async function(event, context) {
    // Autoriser les requêtes CORS
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json'
    };

    // Gérer les pré-requêtes OPTIONS
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200,
            headers,
            body: ''
        };
    }

    // Vérifier la méthode
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            headers,
            body: JSON.stringify({ error: 'Méthode non autorisée' })
        };
    }

    try {
        // Parser les données
        const data = JSON.parse(event.body);
        
        // Validation
        const requiredFields = ['name', 'email', 'subject', 'message'];
        for (const field of requiredFields) {
            if (!data[field] || data[field].trim() === '') {
                return {
                    statusCode: 400,
                    headers,
                    body: JSON.stringify({ 
                        success: false, 
                        error: `Le champ ${field} est requis` 
                    })
                };
            }
        }

        // Validation de l'email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(data.email)) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ 
                    success: false, 
                    error: 'Adresse email invalide' 
                })
            };
        }

        // Ici, vous pouvez:
        // 1. Envoyer un email (via SendGrid, AWS SES, etc.)
        // 2. Sauvegarder dans une base de données
        // 3. Envoyer une notification Slack/Discord
        
        // Pour l'exemple, nous simulons un envoi réussi
        console.log('Nouveau message de contact:', {
            name: data.name,
            email: data.email,
            subject: data.subject,
            timestamp: new Date().toISOString()
        });

        // Simuler un délai
        await new Promise(resolve => setTimeout(resolve, 1000));

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                success: true,
                message: 'Message envoyé avec succès',
                timestamp: new Date().toISOString(),
                data: {
                    name: data.name,
                    email: data.email,
                    subject: data.subject
                }
            })
        };

    } catch (error) {
        console.error('Erreur:', error);
        
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ 
                success: false, 
                error: 'Erreur interne du serveur' 
            })
        };
    }
};