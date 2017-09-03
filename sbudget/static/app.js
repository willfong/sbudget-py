$(document).ready(function() {
  $('.timeago').each(function() {
    var d = $(this)[0]['innerHTML'];
    var newDate = moment(new Date(d)).fromNow();
    $(this).html(newDate);
  });
  $('.fmtdate').each(function() {
    var d = $(this)[0]['innerHTML'];
    var newDate = moment(new Date(d)).format('ddd, MMM Do');
    $(this).html(newDate);
  });
});

function addAmount(typeId) {
  var now = new Date();
  var dateCode = makeDateCode(now);
  $('#monthcode').val(dateCode[0]);
  $('#daycode').val(dateCode[1]);
  $('#type').val(typeId);
  $('#date').val(now);
  $('#form').submit();
}

function makeDateCode(d) {
  var y = d.getFullYear();
  var m = (d.getMonth() + 1 < 10 ? '0' : '') + (d.getMonth() + 1);
  var d = (d.getDate() < 10 ? '0' : '') + d.getDate();
  return [y + m, d];
}
