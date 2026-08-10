class ApiController {
    /**
     * Génère les en-têtes HTTP avec le token d'authentification
     * @returns {Promise<Object>} Les en-têtes HTTP
     */
    static async getHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Token 3d84e3b32c5721c0108d019c1eff1aabc5da5271`
        };
    }

    /**
     * Traite la réponse HTTP et gère les erreurs
     * @param {Response} response - Réponse fetch à traiter
     * @returns {Promise<Object>} Les données JSON de la réponse
     * @throws {Error} Si le statut HTTP indique une erreur
     */
    static async processResponse(response) {
        const responseData = await response.json();
        
        if (response.ok) {
            return responseData;
        } else {
            throw new Error(`Erreur API: ${response.status} - ${responseData.message || 'Erreur inconnue'}`);
        }
    }
}

export { ApiController };