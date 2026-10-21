/* Customer / supplier form: picks the state from the first two digits of a typed GSTIN. */
(function () {
  var gstin = document.getElementById('gstin');
  var state = document.getElementById('state');
  if (!gstin || !state) return;
  gstin.addEventListener('input', function () {
    var code = gstin.value.trim().slice(0, 2);
    if (code.length === 2 && state.querySelector('option[value="' + code + '"]')) state.value = code;
  });
})();
