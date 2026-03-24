// ── Telegram WebApp init ─────────────────────────────────────────────────────
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  // Light mode detection
  if (tg.colorScheme === 'light') {
    document.body.classList.add('tg-light');
  }
}

const INIT_DATA = tg?.initData || '';
const API = '';  // Same origin — Railway'da bot bilan birga

// ── State ────────────────────────────────────────────────────────────────────
let allProducts = [];
let cartItems = [];
let brands = [];
let categories = [];
let activeBrandId = null;
let activeCategoryId = null;
let activeFilter = 'all';
let locationData = { lat: null, lon: null };

// ── Init ─────────────────────────────────────────────────────────────────────
(async function init() {
  try {
    await Promise.all([loadBrands(), loadProducts(), loadCart()]);
  } catch (e) {
    console.error('Init error:', e);
  }
})();

// ── API helpers ──────────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'init-data': INIT_DATA,
    ...(options.headers || {})
  };
  const res = await fetch(API + path, { ...options, headers });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ── Load brands ──────────────────────────────────────────────────────────────
async function loadBrands() {
  try {
    brands = await apiFetch('/api/brands');
    renderBrandChips();
  } catch (e) { console.error('Brands error:', e); }
}

function renderBrandChips() {
  const wrap = document.getElementById('brand-chips');
  wrap.innerHTML = brands.map(b => `
    <button class="filter-chip" data-brand="${b.id}"
      onclick="filterByBrand(${b.id}, this)">
      ${b.emoji || ''} ${b.name}
    </button>
  `).join('');
}

// ── Load products ────────────────────────────────────────────────────────────
async function loadProducts(params = {}) {
  const grid = document.getElementById('products-grid');
  grid.innerHTML = `<div class="skeleton-grid">
    ${Array(4).fill('<div class="skeleton-card"></div>').join('')}
  </div>`;

  try {
    const qs = new URLSearchParams();
    if (params.brand_id) qs.set('brand_id', params.brand_id);
    if (params.category_id) qs.set('category_id', params.category_id);
    if (params.sale) qs.set('sale', 'true');
    allProducts = await apiFetch('/api/products?' + qs.toString());
    renderProducts(allProducts);
  } catch (e) {
    grid.innerHTML = '<p class="no-products">Mahsulotlar yuklanmadi 😕</p>';
  }
}

function renderProducts(products) {
  const grid = document.getElementById('products-grid');
  if (!products.length) {
    grid.innerHTML = '<p class="no-products">Mahsulotlar topilmadi</p>';
    return;
  }
  grid.innerHTML = products.map(p => productCard(p)).join('');
}

function productCard(p) {
  const inCart = cartItems.some(c => c.product_id === p.id);
  const imgHtml = p.photo_id
  ? `<div class="product-img-wrap">
       <img class="product-img" src="/api/photo/${p.photo_id}" 
            onerror="this.style.display='none'" loading="lazy">
       ${p.is_sale ? '<span class="sale-badge">AKSIYA</span>' : ''}
     </div>`
  : `<div class="product-img-wrap">
       <div class="product-img-placeholder">🔧</div>
       ${p.is_sale ? '<span class="sale-badge">AKSIYA</span>' : ''}
     </div>`;

  const oldPrice = p.old_price
    ? `<span class="product-old-price">${formatPrice(p.old_price)}</span>`
    : '';

  return `
    <div class="product-card" onclick="cardTap(event, ${p.id})">
      ${imgHtml}
      <div class="product-info">
        <div class="product-brand">${p.brand_name || ''}</div>
        <div class="product-name">${p.name}</div>
        <div class="product-prices">
          <span class="product-price">${formatPrice(p.price)}</span>
          ${oldPrice}
        </div>
      </div>
      <button class="add-btn ${inCart ? 'added' : ''}"
        data-pid="${p.id}"
        onclick="addToCart(event, ${p.id}, this)">
        ${inCart ? '✓ Savatda' : '+ Savatga'}
      </button>
    </div>
  `;
}

function cardTap(e, productId) {
  // Button bosilganda card tap ishlamasin
  if (e.target.classList.contains('add-btn')) return;
}

// ── Filters ──────────────────────────────────────────────────────────────────
function filterBy(type, el) {
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  activeBrandId = null;
  activeCategoryId = null;
  activeFilter = type;

  const catRow = document.getElementById('category-row');
  catRow.classList.add('hidden');
  catRow.innerHTML = '';

  if (type === 'sale') {
    loadProducts({ sale: true });
  } else {
    loadProducts();
  }
}

async function filterByBrand(brandId, el) {
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  activeBrandId = brandId;
  activeCategoryId = null;

  // Kategoriyalarni yuklash
  try {
    const cats = await apiFetch(`/api/categories?brand_id=${brandId}`);
    renderCategoryChips(cats);
  } catch (e) { console.error(e); }

  loadProducts({ brand_id: brandId });
}

function renderCategoryChips(cats) {
  const row = document.getElementById('category-row');
  if (!cats.length) {
    row.classList.add('hidden');
    return;
  }
  row.classList.remove('hidden');
  row.innerHTML = cats.map((c, i) => `
    <button class="category-chip ${i === 0 ? '' : ''}"
      onclick="filterByCategory(${c.id}, this)">
      ${c.emoji || ''} ${c.name}
    </button>
  `).join('');
}

function filterByCategory(categoryId, el) {
  document.querySelectorAll('.category-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  activeCategoryId = categoryId;
  loadProducts({ category_id: categoryId });
}

// ── Cart operations ──────────────────────────────────────────────────────────
async function loadCart() {
  try {
    cartItems = await apiFetch('/api/cart?init_data=' + encodeURIComponent(INIT_DATA));
    updateCartBadge();
  } catch (e) { cartItems = []; }
}

async function addToCart(event, productId, btn) {
  event.stopPropagation();
  if (btn.classList.contains('added')) return;

  btn.textContent = '...';
  try {
    await apiFetch('/api/cart/add?init_data=' + encodeURIComponent(INIT_DATA), {
      method: 'POST',
      body: JSON.stringify({ product_id: productId })
    });
    await loadCart();
    btn.classList.add('added');
    btn.textContent = '✓ Savatda';
    bumpBadge();
    if (tg?.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
  } catch (e) {
    btn.textContent = '+ Savatga';
    console.error(e);
  }
}

function updateCartBadge() {
  const total = cartItems.reduce((s, i) => s + i.quantity, 0);
  const badge = document.getElementById('cart-badge');
  badge.textContent = total;
  badge.style.display = total > 0 ? 'flex' : 'none';
}

function bumpBadge() {
  const badge = document.getElementById('cart-badge');
  badge.classList.remove('bump');
  void badge.offsetWidth;
  badge.classList.add('bump');
  setTimeout(() => badge.classList.remove('bump'), 300);
}

// ── Cart page ────────────────────────────────────────────────────────────────
function renderCart() {
  const list = document.getElementById('cart-list');
  const empty = document.getElementById('cart-empty');
  const summary = document.getElementById('cart-summary');

  if (!cartItems.length) {
    list.innerHTML = '';
    empty.classList.remove('hidden');
    summary.classList.add('hidden');
    return;
  }

  empty.classList.add('hidden');
  summary.classList.remove('hidden');

  list.innerHTML = cartItems.map(item => `
    <div class="cart-item" id="cart-item-${item.id}">
      <div class="cart-item-img">🔧</div>
      <div class="cart-item-info">
        <div class="cart-item-name">${item.name}</div>
        <div class="cart-item-price">${formatPrice(item.price * item.quantity)}</div>
      </div>
      <div class="qty-controls">
        <button class="qty-btn del" onclick="changeQty(${item.id}, ${item.quantity - 1})">
          ${item.quantity === 1 ? '🗑' : '−'}
        </button>
        <span class="qty-num">${item.quantity}</span>
        <button class="qty-btn" onclick="changeQty(${item.id}, ${item.quantity + 1})">+</button>
      </div>
    </div>
  `).join('');

  const total = cartItems.reduce((s, i) => s + i.price * i.quantity, 0);
  document.getElementById('cart-total-price').textContent = formatPrice(total);
}

async function changeQty(cartId, newQty) {
  try {
    await apiFetch('/api/cart/update?init_data=' + encodeURIComponent(INIT_DATA), {
      method: 'POST',
      body: JSON.stringify({ cart_id: cartId, quantity: newQty })
    });
    await loadCart();
    renderCart();
    if (tg?.HapticFeedback) tg.HapticFeedback.selectionChanged();
  } catch (e) { console.error(e); }
}

// ── Checkout ─────────────────────────────────────────────────────────────────
function fillOrderSummary() {
  const wrap = document.getElementById('order-summary');
  const total = cartItems.reduce((s, i) => s + i.price * i.quantity, 0);
  wrap.innerHTML = `
    ${cartItems.map(i => `
      <div class="order-summary-item">
        <span>${i.name} × ${i.quantity}</span>
        <span>${formatPrice(i.price * i.quantity)}</span>
      </div>
    `).join('')}
    <div class="order-summary-item">
      <span>Jami</span>
      <span>${formatPrice(total)}</span>
    </div>
  `;

  // Telegram user ma'lumotlarini avtomatik to'ldirish
  if (tg?.initDataUnsafe?.user) {
    const u = tg.initDataUnsafe.user;
    const nameInp = document.getElementById('inp-name');
    if (!nameInp.value && (u.first_name || u.last_name)) {
      nameInp.value = [u.first_name, u.last_name].filter(Boolean).join(' ');
    }
  }
}

function requestContact() {
  if (!tg) return;
  tg.requestContact(res => {
    if (res && res.contact) {
      document.getElementById('inp-phone').value = res.contact.phone_number;
    }
  });
}

function requestLocation() {
  const btn = document.getElementById('btn-location');
  const status = document.getElementById('location-status');
  if (!navigator.geolocation) {
    status.textContent = 'Geolokatsiya qo\'llab-quvvatlanmaydi';
    return;
  }
  btn.textContent = '⏳ Aniqlanmoqda...';
  navigator.geolocation.getCurrentPosition(
    pos => {
      locationData.lat = pos.coords.latitude;
      locationData.lon = pos.coords.longitude;
      btn.textContent = '✅ Lokatsiya aniqlandi';
      btn.classList.add('done');
      status.textContent = `${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`;
    },
    () => {
      btn.textContent = '📍 Lokatsiya yuborish';
      status.textContent = 'Ruxsat berilmadi';
    }
  );
}

async function submitOrder() {
  const name = document.getElementById('inp-name').value.trim();
  const phone = document.getElementById('inp-phone').value.trim();

  if (!name) { alert('Ism Familiyangizni kiriting'); return; }
  if (!phone) { alert('Telefon raqamingizni kiriting'); return; }

  const btn = document.querySelector('#page-checkout .btn-primary');
  btn.disabled = true;
  btn.textContent = '⏳ Yuborilmoqda...';

  try {
    const res = await apiFetch('/api/order?init_data=' + encodeURIComponent(INIT_DATA), {
      method: 'POST',
      body: JSON.stringify({
        full_name: name,
        phone: phone,
        latitude: locationData.lat,
        longitude: locationData.lon
      })
    });

    document.getElementById('success-order-id').textContent =
      `Buyurtma #${res.order_id} • ${formatPrice(res.total)}`;
    cartItems = [];
    updateCartBadge();
    showPage('success');
    if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
  } catch (e) {
    alert('Xatolik yuz berdi. Qayta urinib ko\'ring.');
    btn.disabled = false;
    btn.textContent = '✅ Tasdiqlash';
  }
}

// ── Navigation ────────────────────────────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');

  if (name === 'cart') {
    renderCart();
    tg?.BackButton?.show();
    tg?.BackButton?.onClick(() => showPage('catalog'));
  } else if (name === 'checkout') {
    fillOrderSummary();
    tg?.BackButton?.show();
    tg?.BackButton?.onClick(() => showPage('cart'));
  } else {
    tg?.BackButton?.hide();
  }

  window.scrollTo(0, 0);
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function formatPrice(n) {
  return Number(n).toLocaleString('uz-UZ') + " so'm";
}
