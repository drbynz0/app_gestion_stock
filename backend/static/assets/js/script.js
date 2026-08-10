   // Fonctionnalité de base pour le panier
    document.addEventListener('DOMContentLoaded', function() {
        const addToCartButtons = document.querySelectorAll('.add-to-cart');
        const cartCount = document.querySelector('.cart-count');
        let count = 0;
        
        addToCartButtons.forEach(button => {
            button.addEventListener('click', function() {
                const productCard = this.closest('.product-card');
                const productTitle = productCard.querySelector('.product-title').textContent;
                const productPrice = productCard.querySelector('.product-price').textContent;
                
                count++;
                cartCount.textContent = count;
                
                // Animation feedback
                this.textContent = 'Ajouté !';
                this.style.backgroundColor = '#27ae60';
                
                setTimeout(() => {
                    this.textContent = 'Ajouter au panier';
                    this.style.backgroundColor = '#3498db';
                }, 1500);
                
                console.log(`Produit ajouté: ${productTitle} - ${productPrice}`);
            });
        });
    });