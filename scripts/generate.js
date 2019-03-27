function generate() {
    var nReq = new XMLHttpRequest();
    
    nReq.onreadystatechange = function() {
        if (nReq.readyState == 4 && (nReq.status == 200 || nReq.status == 0)) {
            var display = document.getElementById("display");
            display.innerHTML += "<br/>" + nReq.responseText;
			display.scrollTop = display.scrollHeight;
        }
    };
    
    nReq.open("GET","name",true);
    nReq.send(null);
}
