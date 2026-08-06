(function () {
  function closeModal(id) {
    const overlay = document.getElementById(id);
    if (overlay) {
      overlay.classList.remove('open');
    }
  }

  function openModal(id) {
    const overlay = document.getElementById(id);
    if (overlay) {
      overlay.classList.add('open');
    }
  }

  function initModals() {
    document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
      overlay.addEventListener('click', function (event) {
        if (event.target === overlay) {
          overlay.classList.remove('open');
        }
      });
    });

    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') {
        return;
      }
      document.querySelectorAll('.modal-overlay.open').forEach(function (overlay) {
        overlay.classList.remove('open');
      });
    });

    document.querySelectorAll('[data-modal-close]').forEach(function (button) {
      button.addEventListener('click', function () {
        closeModal(button.dataset.modalClose);
      });
    });
  }

  function initAutoDismissAlerts() {
    document.querySelectorAll('.alert[data-auto-dismiss]').forEach(function (alert) {
      const delay = parseInt(alert.dataset.autoDismiss, 10) || 4000;
      window.setTimeout(function () {
        alert.classList.add('alert-hiding');
        window.setTimeout(function () {
          alert.remove();
        }, 350);
      }, delay);
    });
  }

  window.openModal = openModal;
  window.closeModal = closeModal;

  function initUi() {
    initModals();
    initAutoDismissAlerts();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initUi);
  } else {
    initUi();
  }
})();
