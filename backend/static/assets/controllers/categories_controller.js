import { ApiController } from './api_controller.js';
import { AppConstants } from '../constants/constants.js';
class CategoriesController {
    /**
     * Récupère la liste des catégories depuis l'API
     * @returns {Promise<Array>} Liste des catégories
     */
    static async fetchCategories() {
        try {
            const response = await fetch(
                `${AppConstants.BASE_URL}${AppConstants.CATEGORIE_URI}list/`, 
                {
                    method: 'GET',
                    headers: await ApiController.getHeaders()
                }
            );

            return await ApiController.processResponse(response);
        } catch (error) {
            console.log('URL appelée:', `${AppConstants.BASE_URL}${AppConstants.CATEGORIE_URI}list/`);
            console.error('Erreur dans CategoriesService:', error);
            throw error;
        }
    }
}

export { CategoriesController };