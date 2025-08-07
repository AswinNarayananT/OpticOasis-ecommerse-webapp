const API_BASE = '/product';

function checkStatus(productId) {
    fetch(`${API_BASE}/${productId}/check_status/`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        credentials: "same-origin",
    })
    .then(res => res.json())
    .then(data => {
        updateButtonStates(productId, data.in_cart, data.in_wishlist);
    })
    .catch(err => {
        console.error('Error checking status:', err);
    });
}

function updateButtonStates(productId, inCart, inWishlist) {
    const cartBtn = document.getElementById(`cart-btn-${productId}`);
    const wishlistBtn = document.getElementById(`wishlist-btn-${productId}`);

    // Update cart button
    if (cartBtn && inCart !== undefined) {
        if (inCart) {
            cartBtn.classList.add('active');
            cartBtn.title = 'Remove from Cart';
            // Filled cart icon when item is in cart - using simpler filled shopping cart
            cartBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" stroke="none" viewBox="0 0 24 24">
                    <path d="M7 18c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12L8.1 13h7.45c.75 0 1.41-.41 1.75-1.03L21.7 4H5.21l-.94-2H1zm16 16c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                </svg>
            `;
        } else {
            cartBtn.classList.remove('active');
            cartBtn.title = 'Add to Cart';
            // Outline cart icon when item is not in cart - matches your original
            cartBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 7M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17M17 13v4a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-4m8 0V9a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v4"/>
                </svg>
            `;
        }
    }

    // Update wishlist button
    if (wishlistBtn && inWishlist !== undefined) {
        if (inWishlist) {
            wishlistBtn.classList.add('active');
            wishlistBtn.title = 'Remove from Wishlist';
            // Filled heart icon when item is in wishlist - solid heart
            wishlistBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" stroke="none" viewBox="0 0 24 24">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
            `;
        } else {
            wishlistBtn.classList.remove('active');
            wishlistBtn.title = 'Add to Wishlist';
            // Outline heart icon when item is not in wishlist - matches your original
            wishlistBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
            `;
        }
    }
}

function toggleCart(productId) {
    // Add loading state
    const cartBtn = document.getElementById(`cart-btn-${productId}`);
    if (cartBtn) {
        cartBtn.style.pointerEvents = 'none';
        cartBtn.style.opacity = '0.7';
    }

    fetch(`${API_BASE}/toggle_cart/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({ product_id: productId }),
        credentials: "same-origin",
    })
    .then(res => {
        if (res.redirected && res.url.includes('/login')) {
            window.location.href = res.url;
            return;
        }
        return res.json();
    })
    .then(data => {
        if (!data) return;
        
        // Update button state immediately
        updateButtonStates(productId, data.status === "added", undefined);
        
        // Show toast notification
        showToast(
            data.status === "added" ? "Added to cart" : "Removed from cart", 
            data.status === "added" ? "success" : "info"
        );
        
        // Update counts if function exists
        if (typeof updateCounts === 'function') {
            updateCounts();
        }
    })
    .catch(err => {
        console.error('Error toggling cart:', err);
        showToast("Something went wrong. Please try again.", "error");
    })
    .finally(() => {
        // Remove loading state
        if (cartBtn) {
            cartBtn.style.pointerEvents = 'auto';
            cartBtn.style.opacity = '1';
        }
    });
}

function toggleWishlist(productId) {
    // Add loading state
    const wishlistBtn = document.getElementById(`wishlist-btn-${productId}`);
    if (wishlistBtn) {
        wishlistBtn.style.pointerEvents = 'none';
        wishlistBtn.style.opacity = '0.7';
    }

    fetch(`${API_BASE}/toggle_wishlist/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({ product_id: productId }),
        credentials: "same-origin",
    })
    .then(res => {
        if (res.redirected && res.url.includes('/login')) {
            window.location.href = res.url;
            return;
        }
        return res.json();
    })
    .then(data => {
        if (!data) return;
        
        // Update button state immediately
        updateButtonStates(productId, undefined, data.status === "added");
        
        // Show toast notification
        showToast(
            data.status === "added" ? "Added to wishlist" : "Removed from wishlist", 
            data.status === "added" ? "success" : "info"
        );
        
        // Update counts if function exists
        if (typeof updateCounts === 'function') {
            updateCounts();
        }
    })
    .catch(err => {
        console.error('Error toggling wishlist:', err);
        showToast("Something went wrong. Please try again.", "error");
    })
    .finally(() => {
        // Remove loading state
        if (wishlistBtn) {
            wishlistBtn.style.pointerEvents = 'auto';
            wishlistBtn.style.opacity = '1';
        }
    });
}

function showToast(message, level) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            toast: true,
            position: 'top-right',
            icon: level,
            title: message,
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer)
                toast.addEventListener('mouseleave', Swal.resumeTimer)
            }
        });
    } else {
        // Fallback for when SweetAlert2 is not available
        console.log(`${level.toUpperCase()}: ${message}`);
        
        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${level === 'success' ? '#2ecc71' : level === 'error' ? '#e74c3c' : '#3498db'};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10000;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.style.transform = 'translateX(0)', 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }
}

function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === ('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize button states when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Find all product cards and check their status
    const productCards = document.querySelectorAll('[id^="cart-btn-"]');
    productCards.forEach(btn => {
        const productId = btn.id.replace('cart-btn-', '');
        checkStatus(productId);
    });
});