// GitHub Pages API configuration
const TUBEFORGE_API = (window.TUBEFORGE_API || "").replace(/\/$/, "");
const apiUrl = (path) => TUBEFORGE_API ? `${TUBEFORGE_API}${path}` : path;
const $=x=>document.getElementById(x),show=x=>x.classList.remove("hidden"),hide=x=>x.classList.add("hidden");
$("inspect").onclick=async()=>{let url=$("url").value.trim();if(!url)return err("Paste a video URL first.");$("inspect").disabled=true;$("inspect").textContent="Analyzing...";try{let r=await fetch(apiUrl("/api/info"),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url})}),d=await r.json();if(!r.ok)throw Error(d.error);$("thumb").src=d.thumbnail||"";$("title").textContent=d.title||"Video";$("meta").textContent=[d.uploader,d.duration].filter(Boolean).join(" • ");show($("preview"));$("quality").innerHTML='<option value="best">Best available</option>';(d.qualities||[]).forEach(q=>$("quality").insertAdjacentHTML("beforeend",`<option value="${q.height}">${q.label}</option>`));}catch(e){err(e.message)}$("inspect").disabled=false;$("inspect").textContent="Analyze"};
$("format").onchange=()=>{$("quality").disabled=$("format").value!=="video"};
$("download").onclick=async()=>{let url=$("url").value.trim();if(!url)return err("Paste a video URL first.");show($("box"));hide($("file"));$("download").disabled=true;try{let r=await fetch(apiUrl("/api/download"),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,format:$("format").value,height:$("quality").value})}),d=await r.json();if(!r.ok)throw Error(d.error);window.j=d.job_id;poll()}catch(e){err(e.message);$("download").disabled=false}};
$("cancel").onclick=async()=>{if(window.j){$("cancel").disabled=true;$("status").textContent="Cancelling...";await fetch("/api/cancel/"+window.j,{method:"POST"})}};
async function poll(){let d=await (await fetch("/api/status/"+window.j)).json();$("status").textContent=d.status;$("pct").textContent=(d.progress||0)+"%";$("bar").style.width=(d.progress||0)+"%";$("speed").textContent=d.speed||"—";$("size").textContent=(d.downloaded||"—")+" / "+(d.total||"—");$("eta").textContent=d.eta||"—";if(d.status==="complete"){$("status").textContent="Ready!";$("file").href="/download/"+encodeURIComponent(d.filename);show($("file"));$("download").disabled=false;$("cancel").disabled=false;window.j=null}else if(["error","cancelled"].includes(d.status)){err(d.error||"Download cancelled.");$("download").disabled=false;$("cancel").disabled=false;window.j=null}else setTimeout(poll,500)}
function err(x){$("error").textContent=x;show($("error"))}

// Local desktop-style lifecycle:
// when the TubeForge page is closed or navigated away from, ask the local
// Flask process to shut down. sendBeacon is designed for page-exit requests.
(() => {
  let shutdownSent = false;

  function shutdownTubeForge() {
    if (shutdownSent) return;
    shutdownSent = true;

    const endpoint = apiUrl('/api/shutdown');

    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(endpoint, new Blob([], { type: 'text/plain' }));
      } else {
        fetch(endpoint, {
          method: 'POST',
          keepalive: true
        }).catch(() => {});
      }
    } catch (_) {}
  }

  window.addEventListener('pagehide', shutdownTubeForge);
})();
