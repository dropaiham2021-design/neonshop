(function(){
  function rand(min, max) { return Math.random() * (max - min) + min; }

  function start(canvas){
    const ctx = canvas.getContext('2d');
    const DPR = Math.max(1, window.devicePixelRatio || 1);

    const bubbles = [];
    let W, H;

    function resize(){
      const rect = canvas.getBoundingClientRect();
      W = Math.floor(rect.width  * DPR);
      H = Math.floor(rect.height * DPR);
      canvas.width  = W;
      canvas.height = H;
    }

    function addBubbles(n=24){
      bubbles.length = 0;
      for(let i=0;i<n;i++){
        bubbles.push({
          x: rand(0, W),
          y: rand(H*0.6, H*1.1),
          r: rand(10*DPR, 26*DPR),
          vy: rand(0.25*DPR, 0.8*DPR),
          tint: Math.random()
        });
      }
    }

    function draw(){
      ctx.clearRect(0,0,W,H);
      for(const b of bubbles){
        // move
        b.y -= b.vy;
        if(b.y + b.r < -20) { b.y = H + rand(0, H*0.3); b.x = rand(0, W); }

        // radial neon gradient
        const g = ctx.createRadialGradient(b.x-b.r*0.3, b.y-b.r*0.3, 1, b.x, b.y, b.r);
        const teal = 'rgba(33,199,217,';
        const mag  = 'rgba(255,79,163,';
        g.addColorStop(0, 'rgba(255,255,255,0.35)');
        g.addColorStop(0.5, `${b.tint<.5?teal:mag}0.55)`);
        g.addColorStop(1, `${b.tint<.5?teal:mag}0.02)`);

        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.r, 0, Math.PI*2);
        ctx.fill();
      }
      requestAnimationFrame(draw);
    }

    resize(); addBubbles(); draw();
    window.addEventListener('resize', ()=>{ resize(); addBubbles(); });
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('.bubble-canvas').forEach(start);
  });
})();
