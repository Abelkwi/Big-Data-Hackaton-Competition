/**
 * SMARTSAVE API Client
 * Handles all communication with the backend REST API.
 * Uses JWT authentication with automatic token refresh.
 */

/**
 * API Base URL Configuration
 * 
 * By default, the frontend expects the API to be served from the same origin
 * (e.g., running Django locally with `manage.py runserver`).
 * 
 * When hosting the frontend separately from the backend (e.g., frontend on
 * GitHub Pages / Netlify / Vercel and backend on Render), you MUST configure
 * the API_BASE_URL to point to your Render backend URL.
 * 
 * To configure, add a global variable BEFORE loading this script in your HTML:
 *   <script>window.API_BASE_URL = 'https://your-backend.onrender.com/api';</script>
 * 
 * Or set it in this file by uncommenting the line below:
 *   const API_BASE_URL_OVERRIDE = 'https://your-backend.onrender.com/api';
 */
const API = {
    // Use API_BASE_URL from config.js (if loaded), else fall back to same-origin
    BASE_URL: (typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : window.location.origin + '/api').replace(/\/$/, ''),
    
    // ─── Token Management ─────────────────────────────────────
    
    getToken() {
        return localStorage.getItem('access_token');
    },
    
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },
    
    setTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        if (refresh) localStorage.setItem('refresh_token', refresh);
    },
    
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },
    
    isAuthenticated() {
        return !!this.getToken();
    },
    
    getUser() {
        const data = localStorage.getItem('user');
        return data ? JSON.parse(data) : null;
    },
    
    setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    },
    
    // ─── Core Request ─────────────────────────────────────────
    
    async request(method, path, data = null, options = {}) {
        const url = `${this.BASE_URL}${path}`;
        const headers = { 'Content-Type': 'application/json' };
        
        const token = this.getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
        
        const config = {
            method,
            headers: { ...headers, ...options.headers },
        };
        
        if (data && method !== 'GET') {
            config.body = JSON.stringify(data);
        }
        
        if (options.formData) {
            delete headers['Content-Type'];
            config.body = options.formData;
        }
        
        try {
            let response = await fetch(url, config);
            
            // If 401, try refreshing token
            if (response.status === 401 && this.getRefreshToken()) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    headers['Authorization'] = `Bearer ${this.getToken()}`;
                    config.headers = headers;
                    response = await fetch(url, config);
                } else {
                    this.clearTokens();
                    window.location.href = 'login.html';
                    throw new Error('Session expired');
                }
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const json = await response.json();
                if (!response.ok) throw new ApiError(json.detail || JSON.stringify(json), response.status, json);
                return json;
            }
            
            if (!response.ok) throw new ApiError('Request failed', response.status);
            return await response.text();
            
        } catch (err) {
            if (err instanceof ApiError) throw err;
            throw new ApiError(err.message || 'Network error', 0);
        }
    },
    
    async refreshToken() {
        try {
            const res = await fetch(`${this.BASE_URL}/auth/token/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: this.getRefreshToken() }),
            });
            if (res.ok) {
                const data = await res.json();
                this.setTokens(data.access, data.refresh);
                return true;
            }
            return false;
        } catch {
            return false;
        }
    },
    
    // ─── Auth ─────────────────────────────────────────────────
    
    async login(email, password) {
        const data = await this.request('POST', '/auth/login/', { email, password });
        this.setTokens(data.access, data.refresh);
        const profile = await this.request('GET', '/auth/profile/');
        this.setUser(profile);
        return profile;
    },
    
    async register(data) {
        const result = await this.request('POST', '/auth/register/', data);
        return result;
    },
    
    async registerFarmer(data) {
        return await this.request('POST', '/auth/register/farmer/', data);
    },
    
    async registerBuyer(data) {
        return await this.request('POST', '/auth/register/buyer/', data);
    },
    
    async registerNGO(data) {
        return await this.request('POST', '/auth/register/ngo/', data);
    },
    
    async logout() {
        this.clearTokens();
    },
    
    async getProfile() {
        return await this.request('GET', '/auth/profile/');
    },
    
    async updateProfile(data) {
        return await this.request('PUT', '/auth/profile/update/', data);
    },
    
    async changePassword(oldPwd, newPwd) {
        return await this.request('POST', '/auth/profile/change-password/', {
            old_password: oldPwd, new_password: newPwd,
        });
    },
    
    // ─── Marketplace ──────────────────────────────────────────
    
    async getProducts(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return await this.request('GET', `/marketplace/${qs ? '?' + qs : ''}`);
    },
    
    async getProduct(slug) {
        return await this.request('GET', `/marketplace/${slug}/`);
    },
    
    async getCategories() {
        return await this.request('GET', '/marketplace/categories/');
    },
    
    async getFeaturedProducts() {
        return await this.request('GET', '/marketplace/featured/');
    },
    
    async createProduct(data) {
        return await this.request('POST', '/marketplace/create/', data);
    },
    
    async updateProduct(slug, data) {
        return await this.request('PUT', `/marketplace/${slug}/update/`, data);
    },
    
    async deleteProduct(slug) {
        return await this.request('DELETE', `/marketplace/${slug}/delete/`);
    },
    
    async getMyProducts() {
        return await this.request('GET', '/marketplace/my-products/');
    },
    
    async toggleWishlist(slug) {
        return await this.request('POST', `/marketplace/${slug}/wishlist/`);
    },
    
    async getWishlist() {
        return await this.request('GET', '/marketplace/wishlist/');
    },
    
    async addReview(slug, rating, comment) {
        return await this.request('POST', `/marketplace/${slug}/review/`, { rating, comment });
    },
    
    async getPendingVerification() {
        return await this.request('GET', '/marketplace/pending-verification/');
    },
    
    async verifyProduct(slug, action) {
        return await this.request('POST', `/marketplace/${slug}/verify/`, { action });
    },
    
    // ─── Orders ───────────────────────────────────────────────
    
    async getCart() {
        return await this.request('GET', '/orders/cart/');
    },
    
    async addToCart(productId, quantity) {
        return await this.request('POST', '/orders/cart/add/', { product_id: productId, quantity });
    },
    
    async updateCartItem(itemId, quantity) {
        return await this.request('PUT', `/orders/cart/item/${itemId}/`, { quantity });
    },
    
    async removeFromCart(itemId) {
        return await this.request('DELETE', `/orders/cart/item/${itemId}/remove/`);
    },
    
    async clearCart() {
        return await this.request('DELETE', '/orders/cart/clear/');
    },
    
    async checkout(data) {
        return await this.request('POST', '/orders/checkout/', data);
    },
    
    async getOrders() {
        return await this.request('GET', '/orders/');
    },
    
    async getOrder(id) {
        return await this.request('GET', `/orders/${id}/`);
    },
    
    async cancelOrder(id) {
        return await this.request('POST', `/orders/${id}/cancel/`);
    },
    
    async updateOrderStatus(id, status, note = '') {
        return await this.request('POST', `/orders/${id}/status/`, { status, note });
    },
    
    // ─── Messaging ────────────────────────────────────────────
    
    async getConversations() {
        return await this.request('GET', '/messaging/conversations/');
    },
    
    async getConversation(id) {
        return await this.request('GET', `/messaging/conversations/${id}/`);
    },
    
    async createConversation(recipientId, body, subject = '', productId = null) {
        return await this.request('POST', '/messaging/conversations/create/', {
            recipient_id: recipientId, body, subject, product_id: productId,
        });
    },
    
    async sendMessage(conversationId, body) {
        return await this.request('POST', `/messaging/conversations/${conversationId}/send/`, { body });
    },
    
    async getUnreadMessageCount() {
        return await this.request('GET', '/messaging/unread-count/');
    },
    
    // ─── Notifications ────────────────────────────────────────
    
    async getNotifications() {
        return await this.request('GET', '/notifications/');
    },
    
    async markNotificationRead(id) {
        return await this.request('POST', `/notifications/${id}/read/`);
    },
    
    async markAllNotificationsRead() {
        return await this.request('POST', '/notifications/read-all/');
    },
    
    async getUnreadNotificationCount() {
        return await this.request('GET', '/notifications/unread-count/');
    },
    
    // ─── Blog ─────────────────────────────────────────────────
    
    async getPosts(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return await this.request('GET', `/blog/${qs ? '?' + qs : ''}`);
    },
    
    async getPost(slug) {
        return await this.request('GET', `/blog/${slug}/`);
    },
    
    async getBlogCategories() {
        return await this.request('GET', '/blog/categories/');
    },
    
    async addComment(slug, body) {
        return await this.request('POST', `/blog/${slug}/comment/`, { body });
    },
    
    // ─── Innovation ───────────────────────────────────────────
    
    async getIdeas(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return await this.request('GET', `/innovation/${qs ? '?' + qs : ''}`);
    },
    
    async getIdea(slug) {
        return await this.request('GET', `/innovation/${slug}/`);
    },
    
    async createIdea(data) {
        return await this.request('POST', '/innovation/create/', data);
    },
    
    async toggleVote(slug) {
        return await this.request('POST', `/innovation/${slug}/vote/`);
    },
    
    async addIdeaComment(slug, body) {
        return await this.request('POST', `/innovation/${slug}/comment/`, { body });
    },
    
    async getFeaturedIdeas() {
        return await this.request('GET', '/innovation/featured/');
    },
    
    // ─── Recovery ─────────────────────────────────────────────
    
    async getRecoveryListings(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return await this.request('GET', `/recovery/${qs ? '?' + qs : ''}`);
    },
    
    async createRecoveryListing(data) {
        return await this.request('POST', '/recovery/create/', data);
    },
    
    async claimListing(id) {
        return await this.request('POST', `/recovery/${id}/claim/`);
    },
    
    async makeDonation(data) {
        return await this.request('POST', '/recovery/donations/create/', data);
    },
    
    // ─── Contact ──────────────────────────────────────────────
    
    async submitContact(data) {
        return await this.request('POST', '/contact/', data);
    },
    
    // ─── Dashboard ────────────────────────────────────────────
    
    async getFarmerDashboard() {
        return await this.request('GET', '/dashboard/farmer/');
    },
    
    async getBuyerDashboard() {
        return await this.request('GET', '/dashboard/buyer/');
    },
    
    async getNGODashboard() {
        return await this.request('GET', '/dashboard/ngo/');
    },
    
    async getAdminDashboard() {
        return await this.request('GET', '/dashboard/admin/');
    },
    
    // ─── Accounts ─────────────────────────────────────────────
    
    async getFarmers() {
        return await this.request('GET', '/accounts/farmers/');
    },
    
    async getFarmerDetail(slug) {
        return await this.request('GET', `/accounts/farmers/${slug}/`);
    },
    
    async toggleFollow(slug) {
        return await this.request('POST', `/accounts/farmers/${slug}/follow/`);
    },
    
    async getCooperatives() {
        return await this.request('GET', '/accounts/cooperatives/');
    },
    
    // ─── Home ─────────────────────────────────────────────────
    
    async getHomeStats() {
        return await this.request('GET', '/home/stats/');
    },
    
    async getHomeFeatured() {
        return await this.request('GET', '/home/featured-products/');
    },
    
    // ─── Analytics ────────────────────────────────────────────
    
    async getAnalyticsOverview() {
        return await this.request('GET', '/analytics/overview/');
    },
    
    async getTopCrops() {
        return await this.request('GET', '/analytics/top-crops/');
    },
    
    async getActiveDistricts() {
        return await this.request('GET', '/analytics/active-districts/');
    },
};


class ApiError extends Error {
    constructor(message, status, data = null) {
        super(message);
        this.status = status;
        this.data = data;
    }
}


// ─── DOM Helpers ─────────────────────────────────────────────

function $(sel, ctx = document) { return ctx.querySelector(sel); }
function $$(sel, ctx = document) { return [...ctx.querySelectorAll(sel)]; }

function showError(msg, container) {
    const el = document.createElement('div');
    el.className = 'alert alert-error';
    el.textContent = msg;
    el.style.cssText = 'padding:12px 16px;background:#FFEBEE;color:#C62828;border-radius:8px;margin-bottom:16px;font-size:14px;';
    if (container) container.prepend(el);
    setTimeout(() => el.remove(), 5000);
}

function showSuccess(msg, container) {
    const el = document.createElement('div');
    el.className = 'alert alert-success';
    el.textContent = msg;
    el.style.cssText = 'padding:12px 16px;background:#E8F5E9;color:#1B5E20;border-radius:8px;margin-bottom:16px;font-size:14px;';
    if (container) container.prepend(el);
    setTimeout(() => el.remove(), 5000);
}

function formatPrice(amount, currency = 'RWF') {
    const num = parseFloat(amount);
    if (isNaN(num)) return `0 ${currency}`;
    return `${num.toLocaleString()} ${currency}`;
}

function timeAgo(dateStr) {
    const now = new Date();
    const date = new Date(dateStr);
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 2592000) return `${Math.floor(diff / 86400)}d ago`;
    return date.toLocaleDateString();
}

function getQueryParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name) || '';
}