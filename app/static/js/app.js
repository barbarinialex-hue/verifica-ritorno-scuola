document.addEventListener('submit', (event) => {
  const form = event.target;
  const message = form.dataset.confirm;
  if (message && !window.confirm(message)) {
    event.preventDefault();
    return;
  }

  const submitButton = form.querySelector('button[type="submit"]');
  if (submitButton && !form.matches('[enctype="multipart/form-data"]')) {
    submitButton.disabled = true;
    submitButton.dataset.originalLabel = submitButton.textContent;
    submitButton.textContent = 'Invio…';
  }
});
