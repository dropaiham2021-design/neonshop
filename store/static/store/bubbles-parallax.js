// Neon bubbles: seeded everywhere + parallax with mouse/touch
(() => {
  const canvas = document.getElementById('bubble-bg');
  if (!canvas) return;

  const ctx  = canvas.getContext('2d');
  const DPR  = Math.max(1, window.devicePixelRatio || 1);
  const isMobile = /Mobi|Android/i.test(navigator.userAgent);

  // === CONFIG ===
  const CFG = {
    countDesktop: 48,     // bubbles on desktop
    countMobile: 28,      // bubbles on mobile
    radiusMin: 10,        // px (before DPR, depth affects it)
    radiusMax: 28,
    bobSpeedMin: 0.20,    // bobbing speed (smaller = slower)
    bobSpeedMax: 0.60,
    bobDist: 6,           // px bob amplitude (before DPR)
    parallaxMax: 30,      // px max parallax at depth=1
    globalAlpha: 1
  };
  // ==============

  // Respect reduced motion
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced) return;

  let W=0, H=0, raf=0, t=0;
  const bubbles = [];
  const target = {x:0, y:0};   // where we want to parallax to
  const offset = {x:0, y:0};   // smoothed parallax

  function resize(){
    W = Math.round(window.innerWidth  * DPR);
    H = Math.round(window.innerHeight * DPR);
    canvas.width  = W; canvas.height = H;
    canvas.style.width  = '100vw';
    canvas.style.height = '100vh';
  }

  function rand(a,b){ return a + Math.random()*(b-a); }

  function seed(){
    bubbles.length = 0;
    const COUNT = isMobile ? CFG.countMobile : CFG.countDesktop;
    for (let i=0;i<COUNT;i++){
      const depth = rand(0.5, 1.4); // affects parallax and size
      const r = (CFG.radiusMin + Math.random()*(CFG.radiusMax-CFG.radiusMin)) * DPR * depth;
      bubbles.push({
        x: Math.random()*W,
        y: Math.random()*H,
        r,
        d: depth,
        speed: rand(CFG.bobSpeedMin, CFG.bobSpeedMax),
        phase: Math.random()*Math.PI*2,
        tint: Math.random()     // <0.5 teal, else magenta
      });
    }
  }

  function draw(){
    t += 0.016;

    // Ease current parallax toward pointer target
    offset.x += (target.x - offset.x) * 0.07;
    offset.y += (target.y - offset.y) * 0.07;

    ctx.clearRect(0,0,W,H);
    ctx.globalAlpha = CFG.globalAlpha;

    for (const b of bubbles){
      const bob = Math.sin(t*b.speed + b.phase) * (CFG.bobDist*DPR);
      const px = b.x + offset.x * b.d * DPR;
      const py = b.y + offset.y * b.d * DPR + bob;

      const g = ctx.createRadialGradient(
        px - b.r*0.35, py - b.r*0.35, 1, px, py, b.r
      );
      const teal = 'rgba(33,199,217,'; const mag = 'rgba(255,79,163,';
      g.addColorStop(0, 'rgba(255,255,255,0.35)');
      g.addColorStop(0.5, `${b.tint < .5 ? teal : mag}0.55)`);
      g.addColorStop(1, `${b.tint < .5 ? teal : mag}0.02)`);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(px, py, b.r, 0, Math.PI*2); ctx.fill();
    }

    raf = requestAnimationFrame(draw);
  }

  // Convert pointer position to parallax target
  function setTargetFromClient(x, y){
    const nx = x / window.innerWidth  - 0.5; // [-0.5..+0.5]
    const ny = y / window.innerHeight - 0.5;
    target.x = nx * CFG.parallaxMax;
    target.y = ny * CFG.parallaxMax;
  }

  // Mouse & touch
  window.addEventListener('pointermove', e => setTargetFromClient(e.clientX, e.clientY), {passive:true});
  window.addEventListener('touchmove', e => {
    const t = e.touches && e.touches[0]; if (t) setTargetFromClient(t.clientX, t.clientY);
  }, {passive:true});

  // Optional: device tilt for phones (if available/allowed)
  window.addEventListener('deviceorientation', e => {
    if (e.gamma == null || e.beta == null) return;
    const nx = Math.max(-30, Math.min(30, e.gamma)) / 60;   // [-.5..+.5]
    const ny = Math.max(-30, Math.min(30, e.beta - 45)) / 60;
    target.x = nx * CFG.parallaxMax;
    target.y = ny * CFG.parallaxMax;
  });

  function start(){
    cancelAnimationFrame(raf);
    resize(); seed(); draw();
  }
  window.addEventListener('resize', start);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') cancelAnimationFrame(raf);
    else start();
  });

  start();
})();
