/* ═══════════════════════════════════════════════════════════════
   PACTE DE SANG — ambiance globale
   Braises qui montent + tilt 3D sur les éléments [data-tilt].
   Chargé sur toutes les pages via base.html.
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ─── Braises ──────────────────────────────────────────────
    if (!reducedMotion) {
        const embers = document.createElement('div');
        embers.className = 'embers';
        embers.setAttribute('aria-hidden', 'true');
        for (let i = 0; i < 22; i++) {
            const e = document.createElement('span');
            e.className = 'ember';
            e.style.left = Math.random() * 100 + 'vw';
            e.style.setProperty('--dx', (Math.random() * 120 - 60) + 'px');
            e.style.animationDuration = (7 + Math.random() * 9) + 's';
            e.style.animationDelay = (Math.random() * 12) + 's';
            const s = 2 + Math.random() * 2.5;
            e.style.width = s + 'px';
            e.style.height = s + 'px';
            embers.appendChild(e);
        }
        document.body.appendChild(embers);
    }

    // ─── Tilt 3D ──────────────────────────────────────────────
    // S'applique à tout élément portant data-tilt (cartes de rôle,
    // cartes en main…). Le glare suit la souris via --gx/--gy.
    const isCoarse = window.matchMedia('(pointer: coarse)').matches;
    if (reducedMotion || isCoarse) return;

    document.querySelectorAll('[data-tilt]').forEach(function (el) {
        el.addEventListener('mousemove', function (e) {
            const r = el.getBoundingClientRect();
            const x = (e.clientX - r.left) / r.width;
            const y = (e.clientY - r.top) / r.height;
            const rx = (y - 0.5) * -20;
            const ry = (x - 0.5) * 20;
            el.style.transform =
                'rotateX(' + rx + 'deg) rotateY(' + ry + 'deg) translateZ(10px) scale(1.04)';
            el.style.setProperty('--gx', x * 100 + '%');
            el.style.setProperty('--gy', y * 100 + '%');
        });

        el.addEventListener('mouseleave', function () {
            el.style.transition = 'transform .6s cubic-bezier(.2,.8,.2,1)';
            el.style.transform = 'rotateX(0) rotateY(0) translateZ(0) scale(1)';
            setTimeout(function () {
                el.style.transition = 'transform .18s ease-out';
            }, 600);
        });
    });
});
