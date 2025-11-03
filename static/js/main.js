// Common JavaScript functionality for the gallery

document.addEventListener('DOMContentLoaded', function() {
    // Lazy loading images
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Smooth scroll to top
    const scrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    };

    // Show/hide scroll to top button
    let scrollBtn;
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            if (!scrollBtn) {
                scrollBtn = document.createElement('button');
                scrollBtn.className = 'scroll-to-top';
                scrollBtn.innerHTML = '↑';
                scrollBtn.onclick = scrollToTop;
                document.body.appendChild(scrollBtn);
            }
            scrollBtn.style.display = 'block';
        } else if (scrollBtn) {
            scrollBtn.style.display = 'none';
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K for search (if search is implemented)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape to clear filters
        if (e.key === 'Escape') {
            const activeFilter = document.querySelector('.filter-btn.active, .tag.active');
            if (activeFilter && !activeFilter.classList.contains('all')) {
                window.location.href = '/';
            }
        }
    });
});

// Utility function to format numbers (e.g., 1000 -> 1K)
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Toast notification system
const Toast = {
    show: function(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            padding: 1rem 1.5rem;
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            border-radius: 0.5rem;
            box-shadow: var(--shadow-lg);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
            border: 1px solid var(--border-color);
        `;

        if (type === 'success') {
            toast.style.borderColor = 'var(--success)';
        } else if (type === 'error') {
            toast.style.borderColor = 'var(--danger)';
        }

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
};

// Add CSS animations for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .scroll-to-top {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        background-color: var(--accent-primary);
        color: white;
        border: none;
        cursor: pointer;
        font-size: 1.5rem;
        display: none;
        align-items: center;
        justify-content: center;
        box-shadow: var(--shadow-lg);
        transition: all 0.2s;
        z-index: 999;
    }

    .scroll-to-top:hover {
        background-color: var(--accent-hover);
        transform: translateY(-2px);
    }
`;
document.head.appendChild(style);

// Image modal viewer (optional enhancement)
class ImageModal {
    constructor() {
        this.modal = null;
        this.currentImage = null;
    }

    open(imageSrc, imageTitle) {
        if (!this.modal) {
            this.createModal();
        }

        const img = this.modal.querySelector('img');
        const title = this.modal.querySelector('.modal-title');

        img.src = imageSrc;
        title.textContent = imageTitle;
        this.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    close() {
        if (this.modal) {
            this.modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }

    createModal() {
        this.modal = document.createElement('div');
        this.modal.className = 'image-modal';
        this.modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content">
                <button class="modal-close">&times;</button>
                <img src="" alt="">
                <div class="modal-title"></div>
            </div>
        `;

        this.modal.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 2000;
            align-items: center;
            justify-content: center;
        `;

        const overlay = this.modal.querySelector('.modal-overlay');
        overlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.9);
        `;

        const content = this.modal.querySelector('.modal-content');
        content.style.cssText = `
            position: relative;
            max-width: 90vw;
            max-height: 90vh;
            z-index: 2001;
        `;

        const img = this.modal.querySelector('img');
        img.style.cssText = `
            max-width: 100%;
            max-height: 85vh;
            object-fit: contain;
        `;

        const closeBtn = this.modal.querySelector('.modal-close');
        closeBtn.style.cssText = `
            position: absolute;
            top: -2rem;
            right: 0;
            background: none;
            border: none;
            color: white;
            font-size: 2rem;
            cursor: pointer;
            width: 2rem;
            height: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        const title = this.modal.querySelector('.modal-title');
        title.style.cssText = `
            color: white;
            text-align: center;
            margin-top: 1rem;
            font-size: 1.125rem;
        `;

        closeBtn.addEventListener('click', () => this.close());
        overlay.addEventListener('click', () => this.close());

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.close();
            }
        });

        document.body.appendChild(this.modal);
    }
}

// Global instance
window.imageModal = new ImageModal();
