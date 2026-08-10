import { CategoriesController } from '../controllers/categories_controller.js';

class CategoriesService {
    /**
     * Charge et affiche les catégories dans le DOM
     */
    static async loadCategories() {
        const categoriesSection = document.querySelector('.featured-categories .categories-grid');
        
        if (!categoriesSection) {
            console.error('Section des catégories introuvable dans le DOM');
            return;
        }

        // Afficher un loader pendant le chargement
        categoriesSection.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Chargement des catégories...</p>
            </div>
        `;

        try {
            const categories = await CategoriesController.fetchCategories();
            
            if (categories && categories.length > 0) {
                categoriesSection.innerHTML = categories.map(category => `
                    <div class="category-card" data-category-id="${category.id}">
                        <div class="category-image">
                            <img src="${this.getCategoryImage(category.name)}" alt="${category.name}">
                            <div class="category-overlay">
                                <a href="/products.html?category=${category.id}" class="category-link">Voir tous</a>
                            </div>
                        </div>
                        <div class="category-info">
                            <h3>${category.name}</h3>
                            <p>${category.description || 'Découvrez nos produits'}</p>
                        </div>
                    </div>
                `).join('');
            } else {
                categoriesSection.innerHTML = '<p class="no-categories">Aucune catégorie disponible pour le moment.</p>';
            }
        } catch (error) {
            console.error('Erreur lors du chargement des catégories:', error);
            categoriesSection.innerHTML = `
                <p class="error-message">
                    Erreur lors du chargement des catégories. 
                    <button onclick="CategoriesService.loadCategories()">Réessayer</button>
                </p>
            `;
        }
    }

    /**
     * Retourne une image en fonction du nom de la catégorie
     * @param {string} categoryName - Nom de la catégorie
     * @returns {string} URL de l'image
     */
    static getCategoryImage(categoryName) {
        const imagesMap = {
            'smartphone': 'https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80',
            'ordinateur': 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80',
            'accessoire': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80',
            'gaming': 'https://images.unsplash.com/photo-1527814050087-3793815479db?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80',
            'default': 'https://images.unsplash.com/photo-1550009158-9ebf69173e03?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=600&q=80'
        };

        const lowerName = categoryName.toLowerCase();
        for (const [key, url] of Object.entries(imagesMap)) {
            if (lowerName.includes(key)) {
                return url;
            }
        }
        return imagesMap.default;
    }
}

// Charge les catégories au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    CategoriesService.loadCategories();
});

// Rend la méthode disponible globalement pour le bouton "Réessayer"
window.CategoriesService = CategoriesService;

export { CategoriesService };