// constants.js

class AppConstants {
    static APP_NAME = "Bricool App";

    static USER_PASSWORD = "user_password_halal_food_app";
    static USER_EMAIL = "user_email_halal_food_app";

    // API endpoints
    //static BASE_FILE = "https://optionally-willing-raven.ngrok-free.app";
    static BASE_FILE = "http://127.0.0.1:8000";
    static BASE_URL = `${this.BASE_FILE}/api/`;

    static USER_URI = "users/";
    static SELLER_URI = "sellers/";
    static TOKEN_URI = "token/";
    static LOGIN_URI = "login-view/";
    static PASSWORD_RESET = "password_reset/";
    static VERIFY_PASSWORD = "password_reset/verify/";
    static SAVE_PASSWORD = "password_reset/save/";
    static CHANGE_PASSWORD = "password_change/";
    static BANNER_URI = "banners/";
    static STORE_URI = "stores/";
    static SECTION_URI = "sections/";
    static PRODUCT_URI = "products/";
    static CATEGORIE_URI = "categories/";
    static CARD_URI = "cards/";
    static INTERNAL_ORDER_URI = "internal-orders/";
    static EXTERNAL_ORDER_URI = "external-orders/";
    static FACTURE_CLIENT_URI = "factures/clients/";
    static FACTURE_FOURNISSEUR_URI = "factures/fournisseurs/";
    static CUSTOMER_URI = "customers/";
    static SUPPLIER_URI = "suppliers/";
    static DISCOUNT_URI = "discounts/";
    static DELIVERY_NOTE_URI = "delivery-notes/";
    static HISTORICAL_URI = "historical/";
    static DEFAULT_PRODUCT_IMAGE = "https://img.freepik.com/premium-photo/flat-shopping-bag-with-percentage-sign-vector-concept-as-vector-shopping-bag-with-percentage_980716-664374.jpg?w=2000";
}

// Pour utiliser dans d'autres fichiers :
// import { AppConstants } from './constants.js';
export { AppConstants };