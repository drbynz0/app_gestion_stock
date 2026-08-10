import { ProductsController } from '../controllers/products_controller.js';

class AccueilService {
    /**
     * Charge et affiche les produits dans le DOM
     */
    static async loadProducts() {
        const productsSection = document.querySelector('.product-listing .product-grid');
        
        if (!productsSection) {
            console.error('Section des produits introuvable dans le DOM');
            return;
        }

        // Afficher un loader pendant le chargement
        productsSection.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Chargement des produits...</p>
            </div>
        `;

        try {
            const products = await ProductsController.fetchProducts();
            
            if (products && products.length > 0) {
                productsSection.innerHTML = products.map(product => this.createProductCard(product)).join('');
            } else {
                productsSection.innerHTML = '<p class="no-products">Aucun produit disponible pour le moment.</p>';
            }
        } catch (error) {
            console.error('Erreur lors du chargement des produits:', error);
            productsSection.innerHTML = `
                <p class="error-message">
                    Erreur lors du chargement des produits. 
                    <button onclick="AccueilService.loadProducts()">Réessayer</button>
                </p>
            `;
        }
    }

    /**
     * Crée le HTML pour une carte produit
     * @param {Object} product - Données du produit
     * @returns {string} HTML de la carte produit
     */
    static createProductCard(product) {
        const hasPromo = product.on_promo && product.promo_price && product.price;
        let promoBadge = '';
        
        if (hasPromo) {
            const oldPrice = parseFloat(product.price);
            const promoPrice = parseFloat(product.promo_price);
            if (oldPrice > 0 && promoPrice < oldPrice) {
                const percent = Math.round(100 - (promoPrice / oldPrice) * 100);
                promoBadge = `<div class="product-badge promo">-${percent}%</div>`;
            }
        }

        const createdAt = new Date(product.created_at);
        const now = new Date();
        const diffDays = (now - createdAt) / (1000 * 60 * 60 * 24);
        const isNew = diffDays <= 7;

        return `
        <div class="product-card" data-product-id="${product.id}">
            ${isNew ? `<div class="product-badge new">Nouveau</div>` : ''}
            ${hasPromo ? promoBadge : ''}
            <div class="product-image">
                <img src="${product.images?.length > 0 ? product.images[0].image : 'https://img.freepik.com/premium-photo/flat-shopping-bag-with-percentage-sign-vector-concept-as-vector-shopping-bag-with-percentage_980716-664374.jpg?w=2000'}" 
                     alt="${product.name}">
                <div class="quick-view">Voir détails</div>
            </div>
            <div class="product-info">
                <h3>${product.name}</h3>
                <div class="product-meta">
                    <span class="category">${product.category?.name || 'Non catégorisé'}</span>
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
                    ${hasPromo ? `
                        <span class="discounted-price">${product.promo_price} MAD</span>
                        <span class="old-price">${product.price} MAD</span>
                    ` : `<span class="regular-price">${product.price} MAD</span>`}   
                </div>
                <button class="add-to-cart">Ajouter au panier</button>
            </div>
        </div>`;
    }
}

// Charge les produits au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    AccueilService.loadProducts();
});

// Rend la méthode disponible globalement
window.AccueilService = AccueilService;

export { AccueilService };