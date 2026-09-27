<script>(function(){
var st=document.getElementById("cb-status"),btn=document.getElementById("cb-install"),sheet=document.getElementById("cb-sheet"),body=document.getElementById("cb-sheet-body"),deferred=null;
var standalone=window.matchMedia("(display-mode: standalone)").matches||navigator.standalone===true;
function show(h){body.innerHTML=h;sheet.classList.add("on");}
document.getElementById("cb-sheet-close").onclick=function(){sheet.classList.remove("on");};
sheet.onclick=function(e){if(e.target===sheet)sheet.classList.remove("on");};
function status(){var ready=navigator.serviceWorker&&navigator.serviceWorker.controller;st.textContent=(navigator.onLine?"Online":"Offline")+(ready?" · ready offline ✓":"");}
addEventListener("online",status);addEventListener("offline",status);
if(standalone){btn.style.display="none";}
addEventListener("beforeinstallprompt",function(e){e.preventDefault();deferred=e;});
btn.onclick=function(){
 if(deferred){deferred.prompt();deferred.userChoice.finally(function(){deferred=null;});return;}
 var ios=/iphone|ipad|ipod/i.test(navigator.userAgent)||(navigator.platform==="MacIntel"&&navigator.maxTouchPoints>1);
 if(ios){show("<p>In <b>Safari</b>:</p><ol><li>Tap <b>Share</b> (the square with the arrow).</li><li>Tap <b>Add to Home Screen</b>, then <b>Add</b>.</li></ol><p>The ClockBind icon then opens the app, with or without internet.</p>");}
 else if(/Safari/.test(navigator.userAgent)&&!/Chrome|Chromium|Edg/.test(navigator.userAgent)){show("<p>In <b>Safari on the Mac</b>: menu <b>File</b> &rarr; <b>Add to Dock</b>.</p><p>Or open this page in Chrome or Edge and press this button again.</p>");}
 else{show("<p>Use the browser menu: <b>Install ClockBind</b> (Chrome/Edge: the install icon in the address bar, or &#8942; &rarr; <b>Install</b>). On Android: &#8942; &rarr; <b>Add to Home screen</b>.</p>");}
};
if("serviceWorker" in navigator){addEventListener("load",function(){navigator.serviceWorker.register("sw.js").then(function(reg){try{reg.update();}catch(e){}navigator.serviceWorker.ready.then(function(){setTimeout(status,300);});}).catch(function(){});navigator.serviceWorker.addEventListener("controllerchange",status);});}
status();
})();</script>
