/* ============================================================
   优选商城 · 交互脚本
   ============================================================ */
(function () {
  'use strict';

  /* ---------- 数量步进器 ---------- */
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.qty-btn');
    if (!btn) return;
    const stepper = btn.closest('.qty-stepper');
    const input = stepper.querySelector('input');
    if (!input) return;

    const step = parseInt(btn.dataset.step || '1', 10);
    const min = parseInt(input.min || '1', 10);
    const max = parseInt(input.max || '999999', 10);
    let val = parseInt(input.value || '1', 10);

    val = isNaN(val) ? min : val + step;
    if (val < min) val = min;
    if (val > max) val = max;
    input.value = val;

    // 购物车中数量变化自动提交
    const form = input.closest('form.qty-form');
    if (form) form.submit();
  });

  /* ---------- 加入购物车（AJAX，带购物车角标更新） ---------- */
  document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!form.classList.contains('cart-ajax')) return;
    e.preventDefault();

    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.ok) {
          updateCartBadge(data.cart_count);
          toast(data.msg || '已加入购物车', 'success');
        } else {
          toast(data.msg || '操作失败', 'danger');
        }
      })
      .catch(function () { form.submit(); });
  });

  function updateCartBadge(count) {
    const badge = document.getElementById('cartBadge');
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count;
      badge.style.display = '';
      badge.classList.add('pulse');
      setTimeout(function () { badge.classList.remove('pulse'); }, 400);
    } else {
      badge.style.display = 'none';
    }
  }

  /* ---------- 轻提示 ---------- */
  function toast(msg, type) {
    let wrap = document.getElementById('toastWrap');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.id = 'toastWrap';
      wrap.style.cssText =
        'position:fixed;top:80px;right:20px;z-index:2000;display:flex;flex-direction:column;gap:8px';
      document.body.appendChild(wrap);
    }
    const colors = { success: '#16a34a', danger: '#e5484d', warning: '#f59e0b', info: '#0ea5e9' };
    const el = document.createElement('div');
    el.textContent = msg;
    el.style.cssText =
      'background:#fff;border-left:4px solid ' + (colors[type] || colors.info) + ';' +
      'padding:10px 16px;border-radius:10px;box-shadow:0 8px 24px rgba(24,28,45,.14);' +
      'font-size:.9rem;opacity:0;transform:translateX(16px);transition:.25s';
    wrap.appendChild(el);
    requestAnimationFrame(function () {
      el.style.opacity = '1';
      el.style.transform = 'translateX(0)';
    });
    setTimeout(function () {
      el.style.opacity = '0';
      el.style.transform = 'translateX(16px)';
      setTimeout(function () { el.remove(); }, 260);
    }, 2200);
  }

  /* ---------- 后台：图片上传预览 ---------- */
  window.previewImage = function (input) {
    if (!input.files || !input.files[0]) return;
    const reader = new FileReader();
    reader.onload = function (ev) {
      const img = document.getElementById('imgPreview');
      if (img) img.src = ev.target.result;
    };
    reader.readAsDataURL(input.files[0]);
  };

  /* ---------- 自动隐藏成功提示 ---------- */
  document.querySelectorAll('.flash-stack .alert').forEach(function (el, i) {
    setTimeout(function () {
      el.style.transition = 'opacity .3s';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 320);
    }, 2500 + i * 300);
  });
})();
