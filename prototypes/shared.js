/* Shared utilities for all prototypes */

var SizingAPI = (function () {
  'use strict';

  var BASE_URL = window.location.origin;

  // Product types with display names
  var PRODUCT_TYPES = [
    { value: 'leggings', label: 'Leggings' },
    { value: 'capris', label: 'Capris' },
    { value: 'shorts', label: 'Shorts' },
    { value: 'bike_shorts', label: 'Bike Shorts' },
    { value: 'opaque_leggings', label: 'Opaque Leggings' },
    { value: 'opaque_capris', label: 'Opaque Capris' },
    { value: 'high_waist_legging', label: 'High-Waist Legging' },
    { value: 'bras', label: 'Bras' },
    { value: 'braless_tops', label: 'Braless Tops' },
    { value: 'tops_with_bra', label: 'Tops with Bra' },
    { value: 'abdominal_band', label: 'Abdominal Band' },
    { value: 'arm_sleeves', label: 'Arm Sleeves' },
    { value: 'gauntlets', label: 'Gauntlets' },
    { value: 'armbands', label: 'Armbands' },
    { value: 'classic_arm_sleeves', label: 'Classic Arm Sleeves' },
    { value: 'classic_armbands', label: 'Classic Armbands' },
    { value: 'socks', label: 'Socks' },
    { value: 'calf_sleeves', label: 'Calf Sleeves' },
    { value: 'thigh_highs', label: 'Thigh Highs' },
    { value: 'mens_briefs', label: "Men's Briefs" }
  ];

  // Unit conversion helpers
  function inchesToCm(inches) {
    return inches * 2.54;
  }

  function feetInchesToCm(feet, inches) {
    return (feet * 12 + inches) * 2.54;
  }

  function lbsToKg(lbs) {
    return lbs * 0.453592;
  }

  function cmToInches(cm) {
    return cm / 2.54;
  }

  function kgToLbs(kg) {
    return kg / 0.453592;
  }

  // Convert a user-entered value to metric based on field unit and selected system
  function toMetric(value, fieldUnit, useImperial) {
    if (!useImperial) return value;
    if (fieldUnit === 'kg') return lbsToKg(value);
    if (fieldUnit === 'cm') return inchesToCm(value);
    return value;
  }

  // Get display unit label
  function getDisplayUnit(fieldUnit, useImperial) {
    if (!useImperial) return fieldUnit;
    if (fieldUnit === 'kg') return 'lbs';
    if (fieldUnit === 'cm') return 'in';
    return fieldUnit;
  }

  // Fetch measurement fields for a product type
  function getProductFields(productType) {
    return fetch(BASE_URL + '/api/v1/product-fields/' + productType)
      .then(function (r) { return r.json(); });
  }

  // Submit all measurements at once (V1 endpoint)
  function getRecommendation(productType, measurements) {
    return fetch(BASE_URL + '/api/v1/size-recommendation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_type: productType,
        measurements: measurements
      })
    }).then(function (r) { return r.json(); });
  }

  // V2 conversation: start
  function conversationStart(productType, collectAll) {
    return fetch(BASE_URL + '/api/v2/conversation/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_type: productType,
        channel: 'widget',
        collect_all: collectAll || false
      })
    }).then(function (r) { return r.json(); });
  }

  // V2 conversation: answer
  function conversationAnswer(sessionId, value, skip) {
    return fetch(BASE_URL + '/api/v2/conversation/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        answer: {
          value: skip ? null : value,
          skip: skip || false
        }
      })
    }).then(function (r) { return r.json(); });
  }

  // Populate a product type dropdown
  function populateProductSelect(selectEl, defaultValue) {
    selectEl.innerHTML = '';
    PRODUCT_TYPES.forEach(function (pt) {
      var opt = document.createElement('option');
      opt.value = pt.value;
      opt.textContent = pt.label;
      if (pt.value === defaultValue) opt.selected = true;
      selectEl.appendChild(opt);
    });
  }

  // Get product type from URL params
  function getProductFromURL() {
    var params = new URLSearchParams(window.location.search);
    return params.get('product') || 'leggings';
  }

  // Render disproportion warning HTML
  function renderDisproportionWarning(disproportion) {
    if (!disproportion || !disproportion.is_disproportionate) return '';

    var rows = '';
    disproportion.field_mappings.forEach(function (fm) {
      rows += '<tr><td>' + fm.field_label + '</td><td>' +
        fm.value.toFixed(1) + '</td><td><strong>' +
        fm.best_size + '</strong></td></tr>';
    });

    return '<div class="disproportion-warning">' +
      '<h3>Important: Your measurements span multiple sizes</h3>' +
      '<table class="disproportion-table">' +
      '<thead><tr><th>Measurement</th><th>Your Value</th><th>Best Size</th></tr></thead>' +
      '<tbody>' + rows + '</tbody>' +
      '</table>' +
      '<p class="disproportion-note">' + disproportion.notes + '</p>' +
      '</div>';
  }

  // Render result card HTML
  function renderResultCard(result) {
    var confidenceLabel = {
      exact: 'Perfect Match',
      interpolated: 'Close Match',
      out_of_range: 'Outside Standard Range'
    };

    var html = '<div class="result-card">' +
      '<div class="result-size">' + result.recommended_size + '</div>' +
      '<div class="result-confidence ' + result.confidence + '">' +
      (confidenceLabel[result.confidence] || result.confidence) +
      '</div>';

    if (result.notes) {
      html += '<div class="result-notes">' + result.notes + '</div>';
    }

    html += '</div>';

    if (result.disproportion) {
      html += renderDisproportionWarning(result.disproportion);
    }

    return html;
  }

  // Measurement help text by field type
  var FIELD_HELP = {
    height: 'Stand straight against a wall, measure from floor to the top of your head.',
    weight: 'Step on a scale. A rough estimate is fine.',
    upper_arm: 'Measure around the thickest part of your upper arm.',
    forearm: 'Measure around the thickest part of your forearm.',
    wrist: 'Measure snugly around your wrist bone.',
    bust: 'Measure around the fullest part of your bust.',
    underbust: 'Measure snugly just under your bust.',
    waist: 'Measure around your natural waist (narrowest point).',
    hip: 'Measure around the widest part of your hips/buttocks.',
    calf: 'Measure around the thickest part of your calf.',
    ankle: 'Measure snugly around your ankle bone.',
    thigh: 'Measure around the thickest part of your upper thigh.',
    palm: 'Measure around your palm at the knuckles (exclude thumb).',
    hand: 'Measure around the widest part of your hand.',
    leg_length: 'Measure from your crotch down to your ankle bone.'
  };

  function getFieldHelp(fieldName) {
    for (var key in FIELD_HELP) {
      if (fieldName.toLowerCase().indexOf(key) !== -1) {
        return FIELD_HELP[key];
      }
    }
    return 'Use a soft measuring tape. Keep it snug but not tight.';
  }

  return {
    PRODUCT_TYPES: PRODUCT_TYPES,
    inchesToCm: inchesToCm,
    feetInchesToCm: feetInchesToCm,
    lbsToKg: lbsToKg,
    cmToInches: cmToInches,
    kgToLbs: kgToLbs,
    toMetric: toMetric,
    getDisplayUnit: getDisplayUnit,
    getProductFields: getProductFields,
    getRecommendation: getRecommendation,
    conversationStart: conversationStart,
    conversationAnswer: conversationAnswer,
    populateProductSelect: populateProductSelect,
    getProductFromURL: getProductFromURL,
    renderDisproportionWarning: renderDisproportionWarning,
    renderResultCard: renderResultCard,
    getFieldHelp: getFieldHelp
  };
})();
