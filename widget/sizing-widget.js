/**
 * Solidea Sizing Assistant Widget
 * Self-contained JavaScript widget for Shopify product pages.
 * Injects a "Find My Size" button and popup form.
 *
 * Configuration (set before loading this script):
 *   window.SolideaSizingConfig = {
 *     apiUrl: 'https://your-api-url.com',  // required
 *     productType: 'leggings'              // optional override
 *   };
 *
 * ES5-compatible for maximum browser support.
 */
(function () {
  'use strict';

  // --- Configuration ---
  var config = window.SolideaSizingConfig || {};
  var API_URL = config.apiUrl || 'http://localhost:8000';
  var ENDPOINT = API_URL + '/api/v1/size-recommendation';

  // --- Product type definitions ---
  var PRODUCT_TYPES = {
    arm_sleeves: {
      label: 'Arm Sleeves',
      fields: [
        {
          key: 'upper_arm_circumference_cm',
          label: 'Upper Arm Circumference',
          unit: 'cm',
          help: 'Measure around the widest point of your bicep',
        },
        {
          key: 'forearm_circumference_cm',
          label: 'Forearm Circumference',
          unit: 'cm',
          help: 'Measure around the widest point of your forearm, about 1 inch below the elbow',
        },
        {
          key: 'wrist_circumference_cm',
          label: 'Wrist Circumference',
          unit: 'cm',
          help: 'Measure around your wrist, just above the bone',
        },
      ],
    },
    leggings: {
      label: 'Leggings',
      fields: [
        { key: 'height_cm', label: 'Height', unit: 'cm', help: 'Your total height' },
        { key: 'weight_kg', label: 'Weight', unit: 'kg', help: 'Your body weight' },
        {
          key: 'hip_circumference_cm',
          label: 'Hip Circumference',
          unit: 'cm',
          help: 'Measure around the widest point of your hips',
        },
        {
          key: 'waist_circumference_cm',
          label: 'Waist Circumference',
          unit: 'cm',
          help: 'Measure around your natural waistline',
        },
      ],
    },
    capris: {
      label: 'Capris',
      fields: [
        { key: 'height_cm', label: 'Height', unit: 'cm', help: 'Your total height' },
        { key: 'weight_kg', label: 'Weight', unit: 'kg', help: 'Your body weight' },
        {
          key: 'hip_circumference_cm',
          label: 'Hip Circumference',
          unit: 'cm',
          help: 'Measure around the widest point of your hips',
        },
        {
          key: 'waist_circumference_cm',
          label: 'Waist Circumference',
          unit: 'cm',
          help: 'Measure around your natural waistline',
        },
      ],
    },
    socks: {
      label: 'Knee-High Socks',
      fields: [
        {
          key: 'calf_circumference_cm',
          label: 'Calf Circumference',
          unit: 'cm',
          help: 'Measure around the widest part of your calf, about 2 inches below the knee',
        },
        {
          key: 'ankle_circumference_cm',
          label: 'Ankle Circumference',
          unit: 'cm',
          help: 'Measure around the narrowest point of your ankle, just above the bone',
        },
      ],
    },
    bras: {
      label: 'Bras',
      fields: [
        {
          key: 'bust_circumference_cm',
          label: 'Bust Circumference',
          unit: 'cm',
          help: 'Measure around the fullest point of your bust',
        },
        {
          key: 'underbust_circumference_cm',
          label: 'Underbust Circumference',
          unit: 'cm',
          help: 'Measure snugly around your ribcage, just under your breasts',
        },
      ],
    },
  };

  // --- Product type detection from Shopify page ---
  var DETECTION_KEYWORDS = {
    arm_sleeves: ['arm sleeve', 'arm-sleeve', 'armsleeve'],
    leggings: ['legging', 'leggings'],
    capris: ['capri', 'capris'],
    socks: ['sock', 'knee-high', 'knee high', 'mid-calf', 'ankle sock'],
    bras: ['bra ', 'bras', ' bra'],
  };

  function detectProductType() {
    // 1. Check explicit config override
    if (config.productType && PRODUCT_TYPES[config.productType]) {
      return config.productType;
    }

    // 2. Check Shopify product object (available on product pages)
    var searchText = '';
    if (typeof meta !== 'undefined' && meta.product) {
      searchText += ' ' + (meta.product.type || '') + ' ' + (meta.product.tags || []).join(' ');
    }

    // 3. Check page title and URL
    searchText += ' ' + document.title;
    searchText += ' ' + window.location.pathname;
    searchText += ' ' + window.location.href;

    // 4. Check product title element
    var titleEl =
      document.querySelector('.product-single__title') ||
      document.querySelector('.product__title') ||
      document.querySelector('h1.title') ||
      document.querySelector('h1');
    if (titleEl) {
      searchText += ' ' + titleEl.textContent;
    }

    searchText = searchText.toLowerCase();

    var types = Object.keys(DETECTION_KEYWORDS);
    for (var i = 0; i < types.length; i++) {
      var type = types[i];
      var keywords = DETECTION_KEYWORDS[type];
      for (var j = 0; j < keywords.length; j++) {
        if (searchText.indexOf(keywords[j]) !== -1) {
          return type;
        }
      }
    }

    return null; // Could not detect -- show dropdown
  }

  // --- CSS injection ---
  function injectStyles() {
    var css =
      '.solidea-sizing-btn{' +
      'display:inline-flex;align-items:center;gap:8px;' +
      'background:#1a1a2e;color:#fff;border:none;' +
      'padding:12px 24px;font-size:15px;font-family:inherit;' +
      'cursor:pointer;border-radius:0;letter-spacing:0.5px;' +
      'text-transform:uppercase;transition:background 0.2s;margin:10px 0}' +
      '.solidea-sizing-btn:hover{background:#16213e}' +
      '.solidea-sizing-btn svg{width:18px;height:18px;fill:currentColor}' +
      '.solidea-overlay{' +
      'display:none;position:fixed;top:0;left:0;width:100%;height:100%;' +
      'background:rgba(0,0,0,0.5);z-index:99999;' +
      'justify-content:center;align-items:center}' +
      '.solidea-overlay.active{display:flex}' +
      '.solidea-popup{' +
      'background:#fff;max-width:480px;width:92%;max-height:90vh;' +
      'overflow-y:auto;position:relative;padding:0;' +
      'box-shadow:0 8px 32px rgba(0,0,0,0.2)}' +
      '.solidea-popup-header{' +
      'background:#1a1a2e;color:#fff;padding:20px 24px;' +
      'display:flex;justify-content:space-between;align-items:center}' +
      '.solidea-popup-header h2{margin:0;font-size:18px;font-weight:600;' +
      'letter-spacing:0.5px;text-transform:uppercase}' +
      '.solidea-close{background:none;border:none;color:#fff;' +
      'font-size:24px;cursor:pointer;padding:0;line-height:1}' +
      '.solidea-popup-body{padding:24px}' +
      '.solidea-field{margin-bottom:16px}' +
      '.solidea-field label{display:block;font-size:13px;font-weight:600;' +
      'text-transform:uppercase;letter-spacing:0.3px;color:#333;margin-bottom:4px}' +
      '.solidea-field .solidea-help{font-size:12px;color:#777;margin-bottom:6px}' +
      '.solidea-field input,.solidea-field select{' +
      'width:100%;padding:10px 12px;border:1px solid #ccc;' +
      'font-size:15px;font-family:inherit;box-sizing:border-box}' +
      '.solidea-field input:focus,.solidea-field select:focus{' +
      'outline:none;border-color:#1a1a2e}' +
      '.solidea-submit{' +
      'width:100%;background:#c9a96e;color:#fff;border:none;' +
      'padding:14px;font-size:15px;font-weight:600;cursor:pointer;' +
      'text-transform:uppercase;letter-spacing:0.5px;transition:background 0.2s}' +
      '.solidea-submit:hover{background:#b8943e}' +
      '.solidea-submit:disabled{background:#ccc;cursor:not-allowed}' +
      '.solidea-result{margin-top:20px;padding:20px;text-align:center;' +
      'border:2px solid #1a1a2e}' +
      '.solidea-result-size{font-size:48px;font-weight:700;color:#1a1a2e;margin:0}' +
      '.solidea-result-label{font-size:12px;text-transform:uppercase;' +
      'letter-spacing:1px;color:#777;margin-bottom:8px}' +
      '.solidea-result-confidence{font-size:14px;color:#555;margin:8px 0}' +
      '.solidea-result-notes{font-size:13px;color:#777;' +
      'margin-top:12px;line-height:1.5;font-style:italic}' +
      '.solidea-error{color:#c0392b;font-size:14px;margin-top:12px;text-align:center}' +
      '.solidea-spinner{display:inline-block;width:20px;height:20px;' +
      'border:2px solid #fff;border-top-color:transparent;' +
      'border-radius:50%;animation:solidea-spin 0.6s linear infinite}' +
      '@keyframes solidea-spin{to{transform:rotate(360deg)}}' +
      '.solidea-measure-tip{background:#f8f6f1;padding:16px;margin-bottom:20px;' +
      'font-size:13px;line-height:1.5;color:#555;border-left:3px solid #c9a96e}' +
      '@media(max-width:540px){' +
      '.solidea-popup{width:100%;max-width:100%;max-height:100vh;height:100vh}' +
      '.solidea-popup-body{padding:16px}}';

    var style = document.createElement('style');
    style.type = 'text/css';
    style.appendChild(document.createTextNode(css));
    document.head.appendChild(style);
  }

  // --- Build the widget UI ---
  function createWidget(detectedType) {
    // "Find My Size" button
    var btn = document.createElement('button');
    btn.className = 'solidea-sizing-btn';
    btn.innerHTML =
      '<svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 ' +
      '10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21' +
      '.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3' +
      'c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 ' +
      '5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>' +
      'Find My Size';

    // Overlay and popup
    var overlay = document.createElement('div');
    overlay.className = 'solidea-overlay';

    var popup = document.createElement('div');
    popup.className = 'solidea-popup';

    var header = document.createElement('div');
    header.className = 'solidea-popup-header';
    header.innerHTML =
      '<h2>Find Your Size</h2>' + '<button class="solidea-close" aria-label="Close">&times;</button>';

    var body = document.createElement('div');
    body.className = 'solidea-popup-body';

    popup.appendChild(header);
    popup.appendChild(body);
    overlay.appendChild(popup);

    // Build form content
    buildForm(body, detectedType);

    // Event listeners
    btn.addEventListener('click', function () {
      overlay.classList.add('active');
    });

    header.querySelector('.solidea-close').addEventListener('click', function () {
      overlay.classList.remove('active');
    });

    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) {
        overlay.classList.remove('active');
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        overlay.classList.remove('active');
      }
    });

    // Insert button near the add-to-cart button or product form
    var insertTarget =
      document.querySelector('.product-form__buttons') ||
      document.querySelector('.product-form') ||
      document.querySelector('[data-product-form]') ||
      document.querySelector('form[action="/cart/add"]') ||
      document.querySelector('.product__info-wrapper') ||
      document.querySelector('.product-single__meta') ||
      document.querySelector('.product__description');

    if (insertTarget) {
      insertTarget.parentNode.insertBefore(btn, insertTarget.nextSibling);
    } else {
      // Fallback: append after first h1
      var h1 = document.querySelector('h1');
      if (h1 && h1.parentNode) {
        h1.parentNode.insertBefore(btn, h1.nextSibling);
      } else {
        document.body.appendChild(btn);
      }
    }

    document.body.appendChild(overlay);
  }

  function buildForm(container, detectedType) {
    container.innerHTML = '';

    var tip = document.createElement('div');
    tip.className = 'solidea-measure-tip';
    tip.textContent =
      'Use a soft cloth measuring tape on bare skin. Keep the tape snug but not tight. Measure in centimeters.';
    container.appendChild(tip);

    // Product type selector (shown if not auto-detected)
    var currentType = detectedType;
    var typeField = document.createElement('div');
    typeField.className = 'solidea-field';

    if (!detectedType) {
      var typeLabel = document.createElement('label');
      typeLabel.textContent = 'Product Type';
      typeField.appendChild(typeLabel);

      var typeSelect = document.createElement('select');
      typeSelect.id = 'solidea-product-type';

      var defaultOpt = document.createElement('option');
      defaultOpt.value = '';
      defaultOpt.textContent = '-- Select a product --';
      typeSelect.appendChild(defaultOpt);

      var types = Object.keys(PRODUCT_TYPES);
      for (var i = 0; i < types.length; i++) {
        var opt = document.createElement('option');
        opt.value = types[i];
        opt.textContent = PRODUCT_TYPES[types[i]].label;
        typeSelect.appendChild(opt);
      }

      typeField.appendChild(typeSelect);
      container.appendChild(typeField);

      typeSelect.addEventListener('change', function () {
        currentType = typeSelect.value || null;
        renderMeasurementFields(container, currentType, detectedType);
      });
    }

    renderMeasurementFields(container, currentType, detectedType);
  }

  function renderMeasurementFields(container, productType, detectedType) {
    // Remove previous measurement fields, submit, result, error
    var old = container.querySelectorAll(
      '.solidea-measurements,.solidea-submit,.solidea-result,.solidea-error'
    );
    for (var i = 0; i < old.length; i++) {
      old[i].parentNode.removeChild(old[i]);
    }

    if (!productType || !PRODUCT_TYPES[productType]) {
      return;
    }

    var productDef = PRODUCT_TYPES[productType];
    var fieldsWrapper = document.createElement('div');
    fieldsWrapper.className = 'solidea-measurements';

    var fields = productDef.fields;
    for (var j = 0; j < fields.length; j++) {
      var f = fields[j];
      var field = document.createElement('div');
      field.className = 'solidea-field';

      var label = document.createElement('label');
      label.setAttribute('for', 'solidea-' + f.key);
      label.textContent = f.label + ' (' + f.unit + ')';
      field.appendChild(label);

      if (f.help) {
        var help = document.createElement('div');
        help.className = 'solidea-help';
        help.textContent = f.help;
        field.appendChild(help);
      }

      var input = document.createElement('input');
      input.type = 'number';
      input.id = 'solidea-' + f.key;
      input.name = f.key;
      input.min = '0';
      input.step = '0.1';
      input.placeholder = f.label;
      input.required = true;
      field.appendChild(input);

      fieldsWrapper.appendChild(field);
    }

    container.appendChild(fieldsWrapper);

    // Submit button
    var submitBtn = document.createElement('button');
    submitBtn.className = 'solidea-submit';
    submitBtn.type = 'button';
    submitBtn.textContent = 'Find My Size';
    container.appendChild(submitBtn);

    submitBtn.addEventListener('click', function () {
      handleSubmit(productType, fields, submitBtn, container);
    });
  }

  function handleSubmit(productType, fields, submitBtn, container) {
    // Remove old result/error
    var oldResult = container.querySelector('.solidea-result');
    var oldError = container.querySelector('.solidea-error');
    if (oldResult) oldResult.parentNode.removeChild(oldResult);
    if (oldError) oldError.parentNode.removeChild(oldError);

    // Collect measurements
    var measurements = {};
    var valid = true;

    for (var i = 0; i < fields.length; i++) {
      var input = document.getElementById('solidea-' + fields[i].key);
      var val = parseFloat(input.value);
      if (isNaN(val) || val <= 0) {
        valid = false;
        input.style.borderColor = '#c0392b';
      } else {
        input.style.borderColor = '#ccc';
        measurements[fields[i].key] = val;
      }
    }

    if (!valid) {
      var error = document.createElement('div');
      error.className = 'solidea-error';
      error.textContent = 'Please fill in all measurements with valid numbers.';
      container.appendChild(error);
      return;
    }

    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="solidea-spinner"></span>';

    var payload = JSON.stringify({
      product_type: productType,
      measurements: measurements,
    });

    fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Server returned ' + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        showResult(container, data);
      })
      .catch(function (err) {
        var error = document.createElement('div');
        error.className = 'solidea-error';
        error.textContent = 'Unable to get sizing recommendation. Please try again or contact info@solideaus.com.';
        container.appendChild(error);
      })
      .finally(function () {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Find My Size';
      });
  }

  function showResult(container, data) {
    var resultDiv = document.createElement('div');
    resultDiv.className = 'solidea-result';

    var labelEl = document.createElement('div');
    labelEl.className = 'solidea-result-label';
    labelEl.textContent = 'Your Recommended Size';
    resultDiv.appendChild(labelEl);

    var sizeEl = document.createElement('div');
    sizeEl.className = 'solidea-result-size';
    sizeEl.textContent = data.recommended_size || '—';
    resultDiv.appendChild(sizeEl);

    if (data.confidence === 'exact') {
      var confEl = document.createElement('div');
      confEl.className = 'solidea-result-confidence';
      confEl.textContent = 'Exact match based on your measurements';
      resultDiv.appendChild(confEl);
    } else if (data.confidence === 'interpolated') {
      var confEl2 = document.createElement('div');
      confEl2.className = 'solidea-result-confidence';
      confEl2.textContent = 'Close match — see note below';
      resultDiv.appendChild(confEl2);
    } else {
      var confEl3 = document.createElement('div');
      confEl3.className = 'solidea-result-confidence';
      confEl3.textContent = 'Outside standard range — see note below';
      resultDiv.appendChild(confEl3);
    }

    if (data.notes) {
      var notesEl = document.createElement('div');
      notesEl.className = 'solidea-result-notes';
      notesEl.textContent = data.notes;
      resultDiv.appendChild(notesEl);
    }

    container.appendChild(resultDiv);

    // Scroll result into view
    resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // --- Init ---
  function init() {
    injectStyles();
    var detectedType = detectProductType();
    createWidget(detectedType);
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
