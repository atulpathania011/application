/* Shared by the invoice and purchase forms: live totals, add/remove rows, and saved customer/supplier auto-fill. */
(function () {
  var form = document.getElementById('doc-form');
  if (!form) return;
  var body = document.getElementById('items');
  var tpl = document.getElementById('row-tpl');
  var stateEl = document.getElementById('state_code');
  var pick = document.getElementById('party_pick');
  var note = document.getElementById('pick-note');
  var nameEl = document.getElementById('party_name');
  var gstinEl = document.getElementById('party_gstin');
  var addrEl = document.getElementById('party_address');
  var saveEl = document.getElementById('save_party');
  var companyState = form.dataset.companyState;

  var parties = JSON.parse(document.getElementById('parties-data').textContent);
  var byLabel = {}, byGstin = {};
  parties.forEach(function (c) { byLabel[c.label] = c; if (c.gstin) byGstin[c.gstin] = c; });

  function n(v) { var x = parseFloat(v); return isNaN(x) ? 0 : x; }
  function f(x) { return x.toFixed(2); }

  function recalc() {
    var taxable = 0, tax = 0;
    body.querySelectorAll('tr').forEach(function (tr) {
      var t = n(tr.querySelector('[name=qty]').value) * n(tr.querySelector('[name=rate]').value);
      var x = t * n(tr.querySelector('[name=gst]').value) / 100;
      tr.querySelector('.line').textContent = f(t + x);
      taxable += t; tax += x;
    });
    var intra = stateEl.value === companyState;
    var kind = document.getElementById('tax-kind');
    if (kind) kind.textContent = intra
      ? 'Same state as your business: CGST + SGST will be charged.'
      : 'Different state: IGST will be charged.';
    document.getElementById('p-tax-label').textContent = intra ? 'GST (CGST + SGST)' : 'GST (IGST)';
    document.getElementById('p-taxable').textContent = f(taxable);
    document.getElementById('p-tax').textContent = f(tax);
    document.getElementById('p-total').textContent = f(taxable + tax);
  }

  function fill(c) {
    nameEl.value = c.name;
    gstinEl.value = c.gstin;
    addrEl.value = c.address;
    stateEl.value = c.state;
    if (saveEl) saveEl.checked = false;
    if (note) note.textContent = 'Filled from saved details: ' + c.name + '.';
    recalc();
  }

  if (pick) pick.addEventListener('input', function () {
    var c = byLabel[pick.value];
    if (c) fill(c);
  });
  gstinEl.addEventListener('input', function () {
    var v = gstinEl.value.trim().toUpperCase();
    if (v.length >= 2 && stateEl.querySelector('option[value="' + v.slice(0, 2) + '"]')) {
      stateEl.value = v.slice(0, 2);
      recalc();
    }
    if (v.length === 15 && byGstin[v]) fill(byGstin[v]);
  });

  document.getElementById('add-row').addEventListener('click', function () {
    body.appendChild(tpl.content.cloneNode(true));
    recalc();
  });
  body.addEventListener('click', function (e) {
    if (e.target.classList.contains('remove') && body.querySelectorAll('tr').length > 1) {
      e.target.closest('tr').remove();
      recalc();
    }
  });
  form.addEventListener('input', recalc);
  form.addEventListener('change', recalc);
  recalc();
})();
