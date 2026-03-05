/* Consultantt — main application JS */

(function () {
  'use strict';

  // ── State ────────────────────────────────────────────────────────────────
  const state = {
    documents: [],
    selectedDoc: null,
    orderId: null,
    step: 'select', // 'select' | 'payment' | 'status'
  };

  // ── DOM refs ─────────────────────────────────────────────────────────────
  const emailInput       = document.getElementById('emailInput');
  const emailError       = document.getElementById('emailError');
  const docSelector      = document.getElementById('docSelector');
  const docSelectorText  = document.getElementById('docSelectorText');
  const docSelectorPrice = document.getElementById('docSelectorPrice');
  const docDropdown      = document.getElementById('docDropdown');
  const docList          = document.getElementById('docList');
  const docPreviewCard   = document.getElementById('docPreviewCard');
  const docPreviewTitle  = document.getElementById('docPreviewTitle');
  const docPreviewDesc   = document.getElementById('docPreviewDesc');
  const docPreviewPrice  = document.getElementById('docPreviewPrice');
  const docPreviewImgEl  = document.getElementById('docPreviewImgEl');
  const docPreviewImgPlaceholder = document.getElementById('docPreviewImgPlaceholder');
  const proceedBtn       = document.getElementById('proceedBtn');
  const paymentSection   = document.getElementById('paymentSection');
  const kaspiDetails     = document.getElementById('kaspiDetails');
  const bankDetails      = document.getElementById('bankDetails');
  const paymentAmountDisplay = document.getElementById('paymentAmountDisplay');
  const confirmPaymentBtn = document.getElementById('confirmPaymentBtn');
  const statusSection    = document.getElementById('statusSection');
  const statusPending    = document.getElementById('statusPending');
  const statusSuccess    = document.getElementById('statusSuccess');
  const statusError      = document.getElementById('statusError');
  const statusErrorMsg   = document.getElementById('statusErrorMsg');
  const retryBtn         = document.getElementById('retryBtn');
  const paymentRadios    = document.querySelectorAll('input[name="paymentMethod"]');

  // ── Helpers ──────────────────────────────────────────────────────────────
  function formatPrice(price) {
    return Number(price).toLocaleString('ru-KZ') + ' ₸';
  }

  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function csrfHeaders() {
    return {
      'Content-Type': 'application/json',
      'X-CSRFToken': window.CSRF_TOKEN || '',
    };
  }

  function showEmailError(msg) {
    emailError.textContent = msg;
    emailError.classList.remove('hidden');
    emailInput.classList.add('border-red-300');
  }

  function clearEmailError() {
    emailError.classList.add('hidden');
    emailError.textContent = '';
    emailInput.classList.remove('border-red-300');
  }

  // ── Load documents ────────────────────────────────────────────────────────
  async function loadDocuments() {
    try {
      const res = await fetch('/api/documents/');
      const data = await res.json();
      state.documents = data.documents || [];
      renderDocList();
    } catch (err) {
      docList.innerHTML = '<div class="px-4 py-3 text-sm text-red-400">Не удалось загрузить документы.</div>';
    }
  }

  function renderDocList() {
    if (!state.documents.length) {
      docList.innerHTML = '<div class="px-4 py-3 text-sm text-gray-400">Нет доступных документов.</div>';
      return;
    }
    docList.innerHTML = '';
    state.documents.forEach(doc => {
      const div = document.createElement('div');
      div.className = 'doc-option flex items-center justify-between px-4 py-3 cursor-pointer';
      div.innerHTML = `
        <span class="text-sm text-gray-800 pr-2">${doc.title}</span>
        <span class="text-sm font-semibold text-gray-700 flex-shrink-0">${formatPrice(doc.price)}</span>
      `;
      div.addEventListener('click', () => selectDocument(doc));
      docList.appendChild(div);
    });
  }

  function selectDocument(doc) {
    state.selectedDoc = doc;

    docSelectorText.textContent = doc.title;
    docSelectorText.classList.remove('text-gray-400');
    docSelectorText.classList.add('text-gray-800', 'font-medium');

    docSelectorPrice.textContent = formatPrice(doc.price);
    docSelectorPrice.classList.remove('hidden');

    docDropdown.classList.add('hidden');

    // Update preview card
    docPreviewTitle.textContent = doc.title;
    docPreviewDesc.textContent = doc.description;
    docPreviewPrice.textContent = formatPrice(doc.price);

    if (doc.preview_image) {
      docPreviewImgEl.src = doc.preview_image;
      docPreviewImgEl.classList.remove('hidden');
      docPreviewImgPlaceholder.classList.add('hidden');
    } else {
      docPreviewImgEl.classList.add('hidden');
      docPreviewImgPlaceholder.classList.remove('hidden');
    }

    docPreviewCard.classList.remove('hidden');

    updateProceedButton();
  }

  function updateProceedButton() {
    const emailOk = isValidEmail(emailInput.value.trim());
    const docOk = !!state.selectedDoc;
    proceedBtn.disabled = !(emailOk && docOk);
  }

  // ── Dropdown toggle ───────────────────────────────────────────────────────
  docSelector.addEventListener('click', () => {
    docDropdown.classList.toggle('hidden');
  });

  document.addEventListener('click', (e) => {
    if (!docSelector.contains(e.target) && !docDropdown.contains(e.target)) {
      docDropdown.classList.add('hidden');
    }
  });

  // ── Email input live validation ───────────────────────────────────────────
  emailInput.addEventListener('input', () => {
    clearEmailError();
    updateProceedButton();
  });

  emailInput.addEventListener('blur', () => {
    const val = emailInput.value.trim();
    if (val && !isValidEmail(val)) {
      showEmailError('Введите корректный email адрес');
    }
  });

  // ── Proceed to payment ────────────────────────────────────────────────────
  proceedBtn.addEventListener('click', async () => {
    const email = emailInput.value.trim();

    if (!isValidEmail(email)) {
      showEmailError('Введите корректный email адрес');
      emailInput.focus();
      return;
    }

    if (!state.selectedDoc) {
      return;
    }

    proceedBtn.disabled = true;
    proceedBtn.innerHTML = '<svg class="animate-spin" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Создаём заказ...';

    const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked')?.value || 'kaspi';

    try {
      const res = await fetch('/api/orders/create/', {
        method: 'POST',
        headers: csrfHeaders(),
        body: JSON.stringify({
          email: email,
          document_id: state.selectedDoc.id,
          payment_method: paymentMethod,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        showFormError(data.error || 'Ошибка при создании заказа');
        resetProceedBtn();
        return;
      }

      state.orderId = data.order_id;
      paymentAmountDisplay.textContent = formatPrice(state.selectedDoc.price);
      showPaymentSection();

    } catch (err) {
      showFormError('Ошибка соединения. Проверьте интернет.');
      resetProceedBtn();
    }
  });

  function resetProceedBtn() {
    proceedBtn.disabled = false;
    proceedBtn.innerHTML = 'Перейти к оплате <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path d="M9 18l6-6-6-6"/></svg>';
  }

  function showFormError(msg) {
    showEmailError(msg);
  }

  // ── Payment method switch ─────────────────────────────────────────────────
  paymentRadios.forEach(radio => {
    radio.addEventListener('change', () => {
      const labels = document.querySelectorAll('.payment-option');
      labels.forEach(l => {
        l.classList.remove('border-gold', 'bg-opacity-5');
        l.classList.add('border-gray-200');
      });
      const selected = radio.closest('label').querySelector('.payment-option');
      selected.classList.remove('border-gray-200');
      selected.classList.add('border-gold');

      if (radio.value === 'kaspi') {
        kaspiDetails.classList.remove('hidden');
        bankDetails.classList.add('hidden');
      } else {
        kaspiDetails.classList.add('hidden');
        bankDetails.classList.remove('hidden');
      }
    });
  });

  // ── Show/hide sections ─────────────────────────────────────────────────────
  function showPaymentSection() {
    paymentSection.classList.remove('hidden');
    paymentSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    state.step = 'payment';
  }

  function showStatusSection(type) {
    statusSection.classList.remove('hidden');
    statusPending.classList.add('hidden');
    statusSuccess.classList.add('hidden');
    statusError.classList.add('hidden');

    if (type === 'pending') {
      statusPending.classList.remove('hidden');
    } else if (type === 'success') {
      statusSuccess.classList.remove('hidden');
    } else if (type === 'error') {
      statusError.classList.remove('hidden');
    }

    statusSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    state.step = 'status';
  }

  // ── Confirm payment ───────────────────────────────────────────────────────
  confirmPaymentBtn.addEventListener('click', async () => {
    if (!state.orderId) return;

    confirmPaymentBtn.disabled = true;
    confirmPaymentBtn.innerHTML = '<svg class="animate-spin" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Отправляем...';

    try {
      const res = await fetch('/api/orders/confirm-payment/', {
        method: 'POST',
        headers: csrfHeaders(),
        body: JSON.stringify({ order_id: state.orderId }),
      });

      const data = await res.json();

      if (!res.ok) {
        statusErrorMsg.textContent = data.error || 'Не удалось подтвердить оплату.';
        showStatusSection('error');
        paymentSection.classList.add('hidden');
        return;
      }

      showStatusSection('pending');
      paymentSection.classList.add('hidden');

    } catch (err) {
      statusErrorMsg.textContent = 'Ошибка соединения. Попробуйте снова.';
      showStatusSection('error');
    }

    confirmPaymentBtn.disabled = false;
    confirmPaymentBtn.innerHTML = '<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M5 13l4 4L19 7"/></svg> Я оплатил';
  });

  // ── Retry button ──────────────────────────────────────────────────────────
  retryBtn.addEventListener('click', () => {
    statusSection.classList.add('hidden');
    paymentSection.classList.remove('hidden');
    confirmPaymentBtn.disabled = false;
    paymentSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  // ── Init ──────────────────────────────────────────────────────────────────
  loadDocuments();

})();

document.getElementById("confirmPaymentBtn").addEventListener("click", function () {

  const selectedMethod = document.querySelector('input[name="paymentMethod"]:checked');

  if (!selectedMethod) return;

  if (selectedMethod.value === "kaspi") {
    window.open("https://pay.kaspi.kz/pay/jdzlga6x", "_blank");
  }

});