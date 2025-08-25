// Neon bubbles: full-viewport canvas
(() => {
  const canvas = document.getElementById('bubble-bg');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const DPR = Math.max(1, window.devicePixelRatio || 1);
  const isMobile = /Mobi|Android/i.test(navigator.userAgent);
  const COUNT = isMobile ? 22 : 42; // density

  let W = 0, H = 0, raf;
  const bubbles = [];

  function resize(){
    W = Math.round(window.innerWidth  * DPR);
    H = Math.round(window.innerHeight * DPR);
    canvas.width = W;  canvas.height = H;
    canvas.style.width = '100vw';
    canvas.style.height = '100vh';
  }

  function reset(b){
    b.x = Math.random() * W;
    b.y = H + Math.random() * H * 0.3;
    b.r = (10 + Math.random() * 26) * DPR;
    b.vy = (0.25 + Math.random() * 0.8) * DPR;
    b.vx = (Math.random() - 0.5) * 0.15 * DPR;
    b.tint = Math.random(); // teal or magenta
  }

  function seed(){
    bubbles.length = 0;
    for (let i = 0; i < COUNT; i++) {
      const b = {};
      reset(b);
      bubbles.push(b);
    }
  }

  function draw(){
    ctx.clearRect(0,0,W,H);
    for (const b of bubbles){
      b.y -= b.vy;
      b.x += b.vx;
      if (b.y + b.r < -20 || b.x < -b.r || b.x > W + b.r) reset(b);

      const g = ctx.createRadialGradient(
        b.x - b.r*0.3, b.y - b.r*0.3, 1,
        b.x, b.y, b.r
      );
      const teal = 'rgba(33,199,217,';
      const mag  = 'rgba(255,79,163,';
      g.addColorStop(0, 'rgba(255,255,255,0.35)');
      g.addColorStop(0.5, `${b.tint < .5 ? teal : mag}0.55)`);
      g.addColorStop(1, `${b.tint < .5 ? teal : mag}0.03)`);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(b.x, b.y, b.r, 0, Math.PI*2); ctx.fill();
    }
    raf = requestAnimationFrame(draw);
  }

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
