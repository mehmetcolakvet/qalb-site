(function(){
  "use strict";
  var L = document.documentElement.lang === "en" ? "en" : "tr";
  var T = L === "en"
    ? {inhale:"In",hold:"Hold",exhale:"Out",begin:"Begin",stop:"Stop",play:"play",pause:"pause",err:"Could not load right now.",of:"of"}
    : {inhale:"Al",hold:"Tut",exhale:"Ver",begin:"Başlat",stop:"Durdur",play:"çal",pause:"duraklat",err:"Şu an yüklenemedi.",of:"/"};

  /* ---- 1. Yayınlanmış #tr / #en bağlantıları (YouTube kanalı, TikTok açıklamaları) ----
     Aynı belgede hash değişimi sayfayı yeniden yüklemez; bu yüzden hashchange de dinlenir. */
  var routeHash = function(){
    if (L === "tr" && location.hash === "#en") { location.replace("/en/"); return true; }
    if (L === "en" && location.hash === "#tr") { location.replace("/"); return true; }
    return false;
  };
  window.addEventListener("hashchange", routeHash);
  if (routeHash()) return;

  var $ = function(s,r){ return (r||document).querySelector(s); };
  var $$ = function(s,r){ return Array.prototype.slice.call((r||document).querySelectorAll(s)); };
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- 2. Bölüm girişi ---- */
  var rv = $$(".rv");
  if (reduce || !("IntersectionObserver" in window)) {
    rv.forEach(function(e){ e.classList.add("vis"); });
    $$(".path").forEach(function(e){ e.classList.add("vis"); });
  } else {
    var ioFired = false;
    var io = new IntersectionObserver(function(es){
      es.forEach(function(en){ if(en.isIntersecting){ ioFired = true; en.target.classList.add("vis"); io.unobserve(en.target); } });
    }, {threshold:0, rootMargin:"0px 0px -8% 0px"});
    rv.forEach(function(e){ io.observe(e); });
    /* Emniyet ağı: gözlemci hiç ateşlemediyse sayfa boş kalmasın. Ateşlediyse dokunma. */
    setTimeout(function(){
      if (ioFired) return;
      rv.forEach(function(e){ e.classList.add("vis"); });
      $$(".path").forEach(function(e){ e.classList.add("vis"); });
    }, 2500);
    var io2 = new IntersectionObserver(function(es){
      es.forEach(function(en){ if(en.isIntersecting){ en.target.classList.add("vis"); io2.unobserve(en.target); } });
    }, {threshold:0, rootMargin:"0px 0px -8% 0px"});
    $$(".path").forEach(function(e){ io2.observe(e); });
  }

  /* ---- 3. Nefes: 4 sn al · 2 sn tut · 4 sn ver, 60 saniye ---- */
  var ring = $("#ring"), phase = $("#phase"), count = $("#count"), bBtn = $("#bBtn"), bDone = $("#bDone");
  if (ring && bBtn) {
    var timer = null, left = 60, running = false;
    var setPhase = function(sec){
      var p = (60 - sec) % 10;
      phase.textContent = p < 4 ? T.inhale : (p < 6 ? T.hold : T.exhale);
    };
    var fmt = function(s){ return Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2); };
    var stop = function(fin){
      running = false; clearInterval(timer); timer = null;
      ring.classList.remove("run"); bBtn.textContent = T.begin;
      phase.textContent = "1:00"; count.textContent = "";
      if (fin) { bDone.hidden = false; }
    };
    bBtn.addEventListener("click", function(){
      if (running) { stop(false); return; }
      running = true; left = 60; bDone.hidden = true;
      bBtn.textContent = T.stop;
      if (!reduce) ring.classList.add("run");
      setPhase(left); count.textContent = fmt(left);
      timer = setInterval(function(){
        left--;
        if (left <= 0) { stop(true); return; }
        setPhase(left); count.textContent = fmt(left);
      }, 1000);
    });
    window.addEventListener("pagehide", function(){ if (running) stop(false); });
  }

  /* ---- 4. Dil sekmeleri (ilahiler) ---- */
  var tabs = $$(".tab");
  var showLang = function(lang){
    tabs.forEach(function(t){ t.setAttribute("aria-pressed", String(t.dataset.lang === lang)); });
    $$("[data-tlang]").forEach(function(r){ r.hidden = r.dataset.tlang !== lang; });
    $$(".fam").forEach(function(f){
      var any = $$("[data-tlang]", f).some(function(r){ return !r.hidden; });
      f.hidden = !any;
    });
  };
  if (tabs.length) {
    tabs.forEach(function(t, i){
      t.addEventListener("click", function(){ showLang(t.dataset.lang); });
      t.addEventListener("keydown", function(e){
        var d = e.key === "ArrowRight" ? 1 : (e.key === "ArrowLeft" ? -1 : 0);
        if (!d) return;
        e.preventDefault();
        var n = tabs[(i + d + tabs.length) % tabs.length];
        n.focus(); showLang(n.dataset.lang);
      });
    });
    showLang(L === "en" ? "en" : "tr");
  }

  /* ---- 5. Çalar: tek <audio>, preload=none, otomatik başlama yok ---- */
  var au = $("#p"), bar = $("#bar"), npT = $("#npT"), npTime = $("#npTime"), npBtn = $("#npBtn"), npX = $("#npX");
  var status = $("#trkStatus");
  var cur = null, gen = 0;
  var ICON_PLAY = '<svg width="11" height="12" viewBox="0 0 11 12" aria-hidden="true"><path d="M1 1v10l9-5z" fill="currentColor"/></svg>';
  var ICON_PAUSE = '<svg width="10" height="12" viewBox="0 0 10 12" aria-hidden="true"><rect x="0" y="0" width="3" height="12" fill="currentColor"/><rect x="7" y="0" width="3" height="12" fill="currentColor"/></svg>';
  var mmss = function(s){ s = Math.max(0, Math.floor(s||0)); return Math.floor(s/60) + ":" + ("0" + (s%60)).slice(-2); };

  var resetRow = function(r){
    if (!r) return;
    r.classList.remove("load");
    r.classList.remove("err");
    $(".pb", r).innerHTML = ICON_PLAY;
    $(".prog", r).style.transform = "scaleX(0)";
    r.setAttribute("aria-pressed", "false");
    var tl = $(".tl", r);                       /* hata metni dil etiketini ezmişse geri al */
    if (tl && r.dataset.tl) tl.textContent = r.dataset.tl;
  };

  if (au) {
    $$(".trk").forEach(function(r){
      $(".pb", r).innerHTML = ICON_PLAY;
      var tl0 = $(".tl", r);
      if (tl0) r.dataset.tl = tl0.textContent;   /* özgün dil etiketini sakla */
      r.addEventListener("click", function(){
        if (cur === r) {
          if (au.paused) { au.play(); } else { au.pause(); }
          return;
        }
        resetRow(cur);
        cur = r;
        var my = ++gen;                          /* eskimiş play() reddini yok saymak için nesil */
        r.classList.add("load");
        resetRow(r);
        r.classList.add("load");
        au.src = r.dataset.src;
        au.play().catch(function(err){
          if (my !== gen) return;                /* kullanıcı bu arada başka satıra bastı */
          if (err && err.name === "AbortError") return;
          r.classList.remove("load");
          r.classList.add("err");
          var tl = $(".tl", r); if (tl) tl.textContent = T.err;
          if (status) status.textContent = r.dataset.title + " — " + T.err;
          cur = null;
          if (bar) bar.classList.remove("play");
        });
        if (npT) npT.textContent = r.dataset.title + " · Derûnî";
        if (bar) { bar.classList.add("play"); bar.classList.add("on"); }
        if ("mediaSession" in navigator) {
          try {
            navigator.mediaSession.metadata = new MediaMetadata({
              title: r.dataset.title, artist: "Derûnî", album: "Derûnî İlahileri",
              artwork: [{ src: "/assets/logo-256.webp", sizes: "256x256", type: "image/webp" }]
            });
          } catch (e) {}
        }
      });
    });

    au.addEventListener("playing", function(){
      if (!cur) return;
      cur.classList.remove("load");
      $(".pb", cur).innerHTML = ICON_PAUSE;
      cur.setAttribute("aria-pressed", "true");
      if (npBtn) { npBtn.innerHTML = ICON_PAUSE; npBtn.setAttribute("aria-pressed", "true"); }
    });
    au.addEventListener("pause", function(){
      if (cur) { $(".pb", cur).innerHTML = ICON_PLAY; cur.setAttribute("aria-pressed", "false"); }
      if (npBtn) { npBtn.innerHTML = ICON_PLAY; npBtn.setAttribute("aria-pressed", "false"); }
    });
    au.addEventListener("timeupdate", function(){
      if (!cur || !au.duration) return;
      $(".prog", cur).style.transform = "scaleX(" + (au.currentTime / au.duration) + ")";
      if (npTime) npTime.textContent = mmss(au.currentTime) + " / " + mmss(au.duration);
    });
    au.addEventListener("ended", function(){
      resetRow(cur); cur = null;
      if (bar) { bar.classList.remove("play"); if (window.syncBar) window.syncBar(); }
    });
    if (npBtn) npBtn.addEventListener("click", function(){ if (au.paused) { au.play(); } else { au.pause(); } });
    if (npX) npX.addEventListener("click", function(){
      au.pause(); au.removeAttribute("src"); au.load();
      resetRow(cur); cur = null; gen++;
      if (bar) { bar.classList.remove("play"); if (window.syncBar) window.syncBar(); }
    });
    window.addEventListener("pagehide", function(){ au.pause(); });
  }

  /* ---- 6. Alt şerit ---- */
  var hero = $("#hero");
  var heroVisible = true;
  window.syncBar = function(){
    if (!bar) return;
    bar.classList.toggle("on", !heroVisible || bar.classList.contains("play"));
  };
  if (bar && hero) {
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function(es){
        es.forEach(function(en){ heroVisible = en.isIntersecting; });
        window.syncBar();
      }, {threshold:0}).observe(hero);
    } else {
      heroVisible = false;
      window.syncBar();
    }
  }
})();
