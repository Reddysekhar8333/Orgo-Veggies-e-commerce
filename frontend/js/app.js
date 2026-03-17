const state = {
  products: [],
  cart: JSON.parse(localStorage.getItem('ov-cart') || '[]'),
  accessToken: localStorage.getItem('ov-access-token') || '',
};

const templates = {
  header: `
    <header class="site-header sticky-top">
      <nav class="navbar navbar-expand-lg bg-white">
        <div class="container">
          <a class="navbar-brand brand-badge" href="/templates/home.html">Orgo Veggies</a>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div class="collapse navbar-collapse" id="mainNav">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0">
              <li class="nav-item"><a class="nav-link" href="/templates/home.html">Home</a></li>
              <li class="nav-item"><a class="nav-link" href="/templates/products.html">Products</a></li>
              <li class="nav-item"><a class="nav-link" href="/templates/cart.html">Cart</a></li>
              <li class="nav-item"><a class="nav-link" href="/templates/checkout.html">Checkout</a></li>
              <li class="nav-item"><a class="nav-link" href="/templates/seller-dashboard.html">Seller Dashboard</a></li>
            </ul>
            <div class="d-flex gap-2">
              <a class="btn btn-outline-success btn-sm" href="/templates/login.html">Login</a>
              <a class="btn btn-success btn-sm" href="/templates/register.html">Register</a>
            </div>
          </div>
        </div>
      </nav>
    </header>`,
  footer: `<footer class="footer text-center py-4">Fresh produce, delivered responsibly.</footer>`,
};

const api = {
  async request(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (state.accessToken) headers.Authorization = `Bearer ${state.accessToken}`;
    const response = await fetch(`/api/${path}`, { ...options, headers });
    if (!response.ok) throw await response.json().catch(() => ({ detail: 'Request failed' }));
    return response.status === 204 ? null : response.json();
  },
  getProducts(filters = {}) {
    const params = new URLSearchParams(filters);
    return this.request(`products${params.toString() ? `?${params}` : ''}`);
  },
  getProduct(id) { return this.request(`products/${id}`); },
  validateStock(id, quantity) { return this.request(`products/${id}/stock?quantity=${quantity}`); },
  addToCart(payload) { return this.request('cart/add', { method: 'POST', body: JSON.stringify(payload) }); },
  removeFromCart(payload) { return this.request('cart/remove', { method: 'POST', body: JSON.stringify(payload) }); },
  getCart() { return this.request('cart'); },
  placeOrder() { return this.request('order/place', { method: 'POST' }); },
  login(payload) { return this.request('auth/login', { method: 'POST', body: JSON.stringify(payload) }); },
  register(payload) { return this.request('auth/register', { method: 'POST', body: JSON.stringify(payload) }); },
};

function initLayout() {
  const header = document.querySelector('[data-component="header"]');
  const footer = document.querySelector('[data-component="footer"]');
  if (header) header.innerHTML = templates.header;
  if (footer) footer.innerHTML = templates.footer;
}

function saveCartLocally() {
  localStorage.setItem('ov-cart', JSON.stringify(state.cart));
}

function cartTotal() {
  return state.cart.reduce((sum, item) => sum + Number(item.price) * Number(item.quantity), 0).toFixed(2);
}

async function loadProducts() {
  const form = document.getElementById('product-filters');
  const container = document.getElementById('product-grid');
  if (!container) return;

  const fetchAndRender = async (event) => {
    event?.preventDefault();
    const filters = {
      q: form?.querySelector('[name="q"]').value || '',
      min_price: form?.querySelector('[name="min_price"]').value || '',
      max_price: form?.querySelector('[name="max_price"]').value || '',
      in_stock: form?.querySelector('[name="in_stock"]').checked ? 'true' : '',
    };

    state.products = await api.getProducts(filters);
    container.innerHTML = state.products.map((product) => `
      <div class="col-md-6 col-lg-4">
        <div class="card product-card shadow-sm">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title">${product.name}</h5>
            <p class="card-text flex-grow-1">${product.description || 'Fresh and organic produce.'}</p>
            <div class="d-flex justify-content-between align-items-center mb-3">
              <strong>$${product.price}</strong>
              <span class="badge text-bg-${product.stock > 0 ? 'success' : 'danger'} stock-pill">Stock: ${product.stock}</span>
            </div>
            <div class="d-flex gap-2">
              <a href="/templates/product-details.html?id=${product.id}" class="btn btn-outline-secondary btn-sm w-100">Details</a>
              <button class="btn btn-success btn-sm w-100" data-action="add-to-cart" data-product-id="${product.id}" ${product.stock < 1 ? 'disabled' : ''}>Add to cart</button>
            </div>
          </div>
        </div>
      </div>
    `).join('');
  };

  form?.addEventListener('submit', fetchAndRender);
  form?.addEventListener('input', () => fetchAndRender());
  await fetchAndRender();
}

async function addToCart(productId, quantity = 1) {
  const product = state.products.find((item) => item.id === Number(productId));
  if (!product) return;

  try {
    await api.validateStock(productId, quantity);
    await api.addToCart({ product_id: productId, quantity });
  } catch (_error) {
    const existing = state.cart.find((item) => item.product_id === Number(productId));
    if (existing) existing.quantity += quantity;
    else state.cart.push({ product_id: product.id, name: product.name, price: product.price, quantity, stock: product.stock });
    saveCartLocally();
  }

  alert(`${product.name} added to cart.`);
}

async function bindAddToCartButtons() {
  document.body.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-action="add-to-cart"]');
    if (!button) return;
    await addToCart(button.dataset.productId, 1);
  });
}

async function loadProductDetails() {
  const mount = document.getElementById('product-detail');
  if (!mount) return;
  const params = new URLSearchParams(window.location.search);
  const productId = params.get('id');
  if (!productId) return;

  const product = await api.getProduct(productId);
  state.products = [product];
  mount.innerHTML = `
    <div class="card shadow-sm">
      <div class="card-body">
        <h2 class="page-title">${product.name}</h2>
        <p>${product.description || 'No description available.'}</p>
        <p><strong>Price:</strong> $${product.price}</p>
        <label class="form-label">Quantity</label>
        <input id="detail-qty" class="form-control mb-2" type="number" min="1" value="1" />
        <div id="stock-msg" class="small mb-3"></div>
        <button class="btn btn-success" data-action="add-to-cart" data-product-id="${product.id}">Add to cart</button>
      </div>
    </div>`;

  const qtyInput = document.getElementById('detail-qty');
  const stockMsg = document.getElementById('stock-msg');
  qtyInput?.addEventListener('input', async () => {
    const result = await api.validateStock(product.id, qtyInput.value || 1);
    stockMsg.textContent = result.is_available ? 'Quantity available.' : 'Requested quantity exceeds stock.';
    stockMsg.className = `small mb-3 ${result.is_available ? 'text-success' : 'text-danger'}`;
  });
}

async function loadCart() {
  const mount = document.getElementById('cart-table');
  if (!mount) return;

  try {
    state.cart = await api.getCart();
  } catch (_e) {
    state.cart = JSON.parse(localStorage.getItem('ov-cart') || '[]');
  }

  mount.innerHTML = state.cart.length ? state.cart.map((item) => `
    <tr>
      <td>${item.name}</td>
      <td>${item.quantity}</td>
      <td>$${item.price}</td>
      <td><button class="btn btn-sm btn-outline-danger" data-action="remove-cart-item" data-product-id="${item.product_id}">Remove</button></td>
    </tr>
  `).join('') : '<tr><td colspan="4" class="text-center">Your cart is empty.</td></tr>';

  const total = document.getElementById('cart-total');
  if (total) total.textContent = cartTotal();
}

function bindRemoveCartItem() {
  document.body.addEventListener('click', async (event) => {
    const button = event.target.closest('[data-action="remove-cart-item"]');
    if (!button) return;

    const productId = Number(button.dataset.productId);
    try {
      await api.removeFromCart({ product_id: productId });
    } catch (_e) {
      state.cart = state.cart.filter((item) => item.product_id !== productId);
      saveCartLocally();
    }
    await loadCart();
  });
}

function bindCheckout() {
  const form = document.getElementById('checkout-form');
  if (!form) return;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const result = await api.placeOrder();
      alert(`Order #${result.order_id} placed! Total: $${result.total_amount}`);
    } catch (_e) {
      alert('Checkout submitted (demo mode).');
    }
  });
}

function bindAuthForms() {
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(loginForm));
      const result = await api.login(payload);
      state.accessToken = result.access;
      localStorage.setItem('ov-access-token', result.access);
      alert('Login successful');
      window.location.href = '/templates/products.html';
    });
  }

  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(registerForm));
      await api.register(payload);
      alert('Account created. Please login.');
      window.location.href = '/templates/login.html';
    });
  }
}

async function initPage() {
  initLayout();
  await bindAddToCartButtons();
  bindRemoveCartItem();
  await loadProducts();
  await loadProductDetails();
  await loadCart();
  bindCheckout();
  bindAuthForms();
}

document.addEventListener('DOMContentLoaded', initPage);