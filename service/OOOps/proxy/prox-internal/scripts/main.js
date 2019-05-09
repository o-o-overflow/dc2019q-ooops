function split_url(u) {
	u = decodeURIComponent(u); // Stringify
	output = u[0];
	for (i=1;i<u.length;i++) {
		output += u[i]
		if (i%40==0) output+= "<br/>";
	}
	console.log(output)
	return output
}
window.onload = function () { 
	d = document.getElementById("blocked");
	d.innerHTML=(split_url(document.location) + " is blocked")
}
