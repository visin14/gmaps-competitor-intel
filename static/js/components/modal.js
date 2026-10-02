const Modal = {
  isOpen: false,
  
  open(title, bodyHTML, footerHTML = '') {
    const overlay = document.getElementById('modal-overlay');
    const content = document.getElementById('modal-content');
    content.innerHTML = `
      <div class="modal-header">
        <h3>${escapeHtml(title)}</h3>
        <button class="modal-close" onclick="Modal.close()">&times;</button>
      </div>
      <div class="modal-body">${bodyHTML}</div>
      ${footerHTML ? `<div class="modal-footer">${footerHTML}</div>` : ''}
    `;
    overlay.classList.remove('hidden');
    this.isOpen = true;
    document.body.style.overflow = 'hidden';
  },
  
  close() {
    document.getElementById('modal-overlay').classList.add('hidden');
    this.isOpen = false;
    document.body.style.overflow = '';
  },
  
  handleOverlayClick(event) {
    if (event.target === document.getElementById('modal-overlay')) {
      this.close();
    }
  },
  
  confirm(title, message, onConfirm, confirmText = 'Confirm', danger = false) {
    this.open(
      title,
      `<p>${escapeHtml(message)}</p>`,
      `<button class="btn btn-secondary" onclick="Modal.close()">Cancel</button>
       <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" onclick="(${onConfirm.toString()})(); Modal.close();">${confirmText}</button>`
    );
  }
};

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && Modal.isOpen) Modal.close();
});
