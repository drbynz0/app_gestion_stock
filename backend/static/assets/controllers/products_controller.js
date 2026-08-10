import { ApiController } from './api_controller.js';
import { AppConstants } from '../constants/constants.js';
class ProductsController {
    /**
     * Récupère la liste des produits depuis l'API
     * @returns {Promise<Array>} Liste des produits
     */
    static async fetchProducts() {
        try {
            const response = await fetch(
                `${AppConstants.BASE_URL}${AppConstants.PRODUCT_URI}list/`, 
                {
                    method: 'GET',
                    headers: await ApiController.getHeaders()
                }
            );

            return await ApiController.processResponse(response);
        } catch (error) {
            console.log('URL appelée:', `${AppConstants.BASE_URL}${AppConstants.PRODUCT_URI}list/`);
            console.error('Erreur dans ProductsService:', error);
            throw error;
        }
    }
}

export { ProductsController };