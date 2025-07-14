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
        const cartBtn = document.getElementById(`cart-btn-${productId}`);
        const wishlistBtn = document.getElementById(`wishlist-btn-${productId}`);

        if (cartBtn) {
            cartBtn.style.backgroundColor = data.in_cart ? "#28a745" : "#222";
        }
        if (wishlistBtn) {
            wishlistBtn.style.backgroundColor = data.in_wishlist ? "#dc3545" : "#222";
        }
    })
    .catch(err => {
        console.error('Error checking status:', err);
    });
}

function toggleCart(productId) {
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
            window.location.href = res.url; // redirect to login page
            return;
        }
        return res.json();
    })
    .then(data => {
        if (!data) return;
        checkStatus(productId);
        showToast(data.status === "added" ? "Added to cart" : "Removed from cart", data.status === "added" ? "success" : "error");
        updateCounts();  // 🔥 Call this after the action
    })
    .catch(err => {
        console.error('Error toggling cart:', err);
    });
}

function toggleWishlist(productId) {
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
            window.location.href = res.url; // redirect to login page
            return;
        }
        return res.json();
    })
    .then(data => {
        if (!data) return;
        checkStatus(productId);
        showToast(data.status === "added" ? "Added to wishlist" : "Removed from wishlist", data.status === "added" ? "success" : "error");
        updateCounts();  // 🔥 Call this after the action
    })
    .catch(err => {
        console.error('Error toggling wishlist:', err);
    });
}


function showToast(message, level) {
    Swal.fire({
        toast: true,
        position: 'top-right',
        icon: level,
        title: message,
        showConfirmButton: false,
        timer: 3000
    });
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
