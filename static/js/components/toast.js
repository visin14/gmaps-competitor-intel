const Toast = {
  _icons: { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' },
  
  show(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${this._icons[type] || 'i'}</span>
      <span class="toast-message">${escapeHtml(message)}</span>
      <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(toast);
    // Trigger animation
    requestAnimationFrame(() => toast.classList.add('toast-visible'));
    // Auto remove
    setTimeout(() => {
      toast.classList.remove('toast-visible');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },
  
  success: function(msg) { this.show(msg, 'success'); },
  error: function(msg) { this.show(msg, 'error'); },
  warning: function(msg) { this.show(msg, 'warning'); },
  info: function(msg) { this.show(msg, 'info'); },
};
