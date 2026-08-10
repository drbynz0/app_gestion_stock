import { ProductsController } from '../controllers/products_controller.js';

class PromoService {
    /**
     * Charge et affiche les catégories dans le DOM
     */
    static async loadPromo() {
        const promoGrid = document.getElementById('promo-products');
        if (!promoGrid) {
            console.error('Section des promotions introuvable dans le DOM');
            return;
        }

        // Afficher un loader pendant le chargement
        promoGrid.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Chargement des promotions...</p>
            </div>
        `;

        try {
            const products = await ProductsController.fetchProducts();
            
if (products.length > 0) {
                promoGrid.innerHTML = products.map(product => {
                    const hasPromo = product.on_promo && product.promo_price && product.price;
                    let promoBadge = '';
                    if (hasPromo) {
                        const oldPrice = parseFloat(product.price);
                        const promoPrice = parseFloat(product.promo_price);
                        if (oldPrice > 0 && promoPrice < oldPrice) {
                            const percent = Math.round(100 - (promoPrice / oldPrice) * 100);
                            promoBadge = `<div class="product-badge promo">-${percent}%</div>`;
                        }

                        return `
                        <div class="product-card" data-product-id="${product.id}">
                            ${product.on_promo ? promoBadge : ''}
                            <div class="product-image">
                                <img src="${product.images && product.images.length > 0 ? product.images[0].image : 'https://img.freepik.com/premium-photo/flat-shopping-bag-with-percentage-sign-vector-concept-as-vector-shopping-bag-with-percentage_980716-664374.jpg?w=2000'}" alt="${product.name}">
                                <div class="quick-view">Voir détails</div>
                            </div>
                            <div class="product-info">
                                <h3>${product.name}</h3>
                                <div class="product-meta">
                                    <span class="rating">
                                        <i class="fas fa-star"></i>
                                        <i class="fas fa-star"></i>
                                        <i class="fas fa-star"></i>
                                        <i class="fas fa-star"></i>
                                        <i class="fas fa-star-half-alt"></i>
                                        <span>(24)</span>
                                    </span>
                                </div>
                                <div class="price">
                                    ${product.on_promo ? `<span class="discounted-price">${product.promo_price} MAD</span>
                                    <span class="old-price">${product.price} MAD</span>` :  `<span class="regular-price">${product.price} MAD</span>`}   
                                </div>
                                <button class="add-to-cart">Ajouter au panier</button>
                            </div>
                        </div> `;
                    }
                }).join('');
            } else {
                promoGrid.innerHTML = '<p class="no-products">Aucune promotion disponible pour le moment.</p>';
            }
        } catch (error) {
            console.error('Erreur lors du chargement des catégories:', error);
            categoriesSection.innerHTML = `
                <p class="error-message">
                    Erreur lors du chargement des promotions. 
                    <button onclick="PromotionsService.loadPromo()">Réessayer</button>
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
    PromoService.loadPromo();
});

// Rend la méthode disponible globalement pour le bouton "Réessayer"
window.PromoService = PromoService;

export { PromoService };