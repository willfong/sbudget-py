$(document).ready(function() {});
function addAmount(typeId) {
  var amount = $('#amount')[0].value;
  var now = new Date();
  var dateCode = makeDateCode(now);
  $.post('addAmount', {
    date: now,
    monthcode: dateCode[0],
    daycode: dateCode[1],
    type: typeId,
    amount: amount
  }).then(() => {
    $('#amount')[0].value = '';
    $('#alertMsg').toggleClass('hidden');
  });
}

function makeDateCode(d) {
  var y = d.getFullYear();
  var m = (d.getMonth() + 1 < 10 ? '0' : '') + (d.getMonth() + 1);
  var d = (d.getDate() < 10 ? '0' : '') + d.getDate();
  return [y + m, d];
}
