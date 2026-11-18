import { useEffect, useMemo, useState } from "react";

import { getProducts } from "../api/products.js";
import { createOrder } from "../api/orders.js";
import { Header } from "../components/layout/Header.jsx";
import { Icon } from "../components/ui/Icon.jsx";
import { CartPanel } from "../features/cart/CartPanel.jsx";
import { OrderConfirmation } from "../features/orders/OrderConfirmation.jsx";
import { ProductCard } from "../features/products/ProductCard.jsx";

export default function App() {
  const [activeCategory, setActiveCategory] = useState("All");
  const [search, setSearch] = useState("");
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [reloadCount, setReloadCount] = useState(0);
  const [isSubmittingOrder, setIsSubmittingOrder] = useState(false);
  const [orderError, setOrderError] = useState("");
  const [completedOrder, setCompletedOrder] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadProducts() {
      setIsLoading(true);
      setLoadError("");

      try {
        const result = await getProducts({ signal: controller.signal });
        if (!Array.isArray(result)) {
          throw new Error("The product service returned an invalid response.");
        }
        setProducts(result);
      } catch {
        if (!controller.signal.aborted) {
          setLoadError(
            "We couldn't load the product collection. Check that the API and database are running, then try again.",
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    loadProducts();
    return () => controller.abort();
  }, [reloadCount]);

  const categories = useMemo(
    () => ["All", ...new Set(products.map((product) => product.category))],
    [products],
  );

  const visibleProducts = useMemo(() => {
    const query = search.trim().toLowerCase();

    return products.filter((product) => {
      const matchesCategory =
        activeCategory === "All" || product.category === activeCategory;
      const matchesSearch =
        query.length === 0 ||
        `${product.name} ${product.description}`.toLowerCase().includes(query);

      return matchesCategory && matchesSearch;
    });
  }, [activeCategory, products, search]);

  const cartCount = cart.reduce((total, item) => total + item.quantity, 0);

  function addToCart(product) {
    setCart((items) => {
      const existing = items.find((item) => item.id === product.id);

      if (existing) {
        if (existing.quantity >= product.stock_quantity) {
          return items;
        }
        return items.map((item) =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item,
        );
      }

      return [...items, { ...product, quantity: 1 }];
    });
  }

  function updateQuantity(productId, quantity) {
    const product = products.find((item) => item.id === productId);
    const availableQuantity = product?.stock_quantity ?? 0;
    const nextQuantity = Math.min(quantity, availableQuantity);

    setCart((items) => {
      if (nextQuantity < 1) {
        return items.filter((item) => item.id !== productId);
      }
      return items.map((item) =>
        item.id === productId ? { ...item, quantity: nextQuantity } : item,
      );
    });
  }

  async function submitOrder() {
    if (cart.length === 0 || isSubmittingOrder) {
      return;
    }

    setIsSubmittingOrder(true);
    setOrderError("");
    try {
      const order = await createOrder(
        cart.map((item) => ({
          product_id: item.id,
          quantity: item.quantity,
        })),
      );
      setCart([]);
      setCartOpen(false);
      setCompletedOrder(order);
      setReloadCount((count) => count + 1);
    } catch (error) {
      setOrderError(
        error instanceof Error
          ? error.message
          : "We couldn't place your order. Please try again.",
      );
    } finally {
      setIsSubmittingOrder(false);
    }
  }

  return (
    <div className="site-shell">
      <div className="announcement">
        <span>Small upgrades, better everyday.</span>
        <span className="announcement-note">Thoughtfully picked for you</span>
      </div>

      <Header cartCount={cartCount} onCartClick={() => setCartOpen(true)} />

      <main>
        <section className="hero page-width" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="eyebrow"><span className="eyebrow-dot" /> THE GOOD
              GOODS EDIT</p>
            <h1 id="hero-title">
              Good things,
              <br />
              <span>made useful.</span>
            </h1>
            <p className="hero-description">
              The little things that make your desk, your day, and everything
              in between feel a little better.
            </p>
            <a className="button button-dark hero-button" href="#shop">
              Explore the collection <Icon name="arrowRight" />
            </a>
            <div className="hero-proof">
              <div className="avatar-stack" aria-hidden="true">
                <span>R</span><span>M</span><span>A</span>
              </div>
              <p><strong>Good picks, good people.</strong><br />A collection
                built around the everyday.</p>
            </div>
          </div>

          <div className="hero-art" aria-label="Featured everyday essentials">
            <div className="hero-sun" />
            <span className="hero-art-label">THE EVERYDAY EDIT · NO. 01</span>
            <div className="hero-orbit hero-orbit-one" />
            <div className="hero-orbit hero-orbit-two" />
            <div className="hero-product hero-product-bottle" aria-hidden="true">
              <span className="bottle-cap" />
              <span className="bottle-mark">good<br />form</span>
            </div>
            <div className="hero-product hero-product-notebook" aria-hidden="true">
              <span>MAKE<br />SPACE<br />TO THINK.</span>
              <i>01 / 04</i>
            </div>
            <div className="hero-product hero-product-cup" aria-hidden="true">
              <span className="cup-handle" />
              <span className="cup-mark">slow<br />mornings</span>
            </div>
            <div className="hero-sticker"><span>MADE FOR</span><strong>real<br />life</strong><i>✳</i></div>
            <p className="hero-art-caption">Useful by nature. Lovely by design.</p>
          </div>
        </section>

        <section className="benefit-strip" aria-label="Store benefits" id="about">
          <div className="benefit-inner page-width">
            <p><Icon name="sparkle" /> Considered essentials</p>
            <span className="benefit-divider" />
            <p><Icon name="leaf" /> Less, but better</p>
            <span className="benefit-divider" />
            <p><Icon name="heart" /> Made for everyday</p>
          </div>
        </section>

        <section className="shop-section page-width" id="shop">
          <div className="section-heading">
            <div>
              <p className="eyebrow">A FEW OF OUR FAVORITES</p>
              <h2>Find your everyday.</h2>
            </div>
            <label className="search-box">
              <Icon name="search" />
              <span className="visually-hidden">Search products</span>
              <input
                type="search"
                placeholder="What are you looking for?"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <kbd>/</kbd>
            </label>
          </div>

          <div className="shop-toolbar">
            <div className="category-list" aria-label="Filter by category">
              {categories.map((category) => (
                <button
                  className={`category-chip${activeCategory === category ? " is-active" : ""}`}
                  key={category}
                  type="button"
                  aria-pressed={activeCategory === category}
                  onClick={() => setActiveCategory(category)}
                >
                  {category}
                </button>
              ))}
            </div>
            <span className="product-count">
              {visibleProducts.length.toString().padStart(2, "0")} pieces
            </span>
          </div>

          {isLoading ? (
            <div className="product-state" role="status" aria-live="polite">
              Loading products…
            </div>
          ) : loadError ? (
            <div className="product-state product-state-error" role="alert">
              <h3>Products are unavailable</h3>
              <p>{loadError}</p>
              <button
                className="button button-dark"
                onClick={() => setReloadCount((count) => count + 1)}
                type="button"
              >
                Try again
              </button>
            </div>
          ) : products.length === 0 ? (
            <div className="product-state" role="status">
              <h3>No products yet</h3>
              <p>There are no products in the catalog right now.</p>
            </div>
          ) : visibleProducts.length > 0 ? (
            <div className="product-grid">
              {visibleProducts.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onAdd={() => addToCart(product)}
                />
              ))}
            </div>
          ) : (
            <div className="empty-search">
              <span aria-hidden="true">⌕</span>
              <h3>No pieces found</h3>
              <p>Try another search or choose a different category.</p>
              <button
                className="text-button"
                onClick={() => {
                  setSearch("");
                  setActiveCategory("All");
                }}
                type="button"
              >
                Clear filters <Icon name="arrowRight" />
              </button>
            </div>
          )}
        </section>
      </main>

      <footer className="site-footer">
        <div className="page-width footer-inner">
          <a href="#" className="brand footer-brand" aria-label="Softspace home">
            <span className="brand-mark"><span /><span /><span /><span /></span>
            <span>soft<span className="brand-light">space</span></span>
          </a>
          <p>Useful things for the everyday.</p>
          <span>© 2026 Softspace · Made for real life</span>
        </div>
      </footer>

      <CartPanel
        cart={cart}
        isOpen={cartOpen}
        onClose={() => setCartOpen(false)}
        onQuantityChange={updateQuantity}
        onPlaceOrder={submitOrder}
        isSubmitting={isSubmittingOrder}
        orderError={orderError}
      />
      <OrderConfirmation
        order={completedOrder}
        onClose={() => setCompletedOrder(null)}
      />
      {cartOpen && (
        <button
          aria-label="Close shopping cart"
          className="cart-backdrop"
          onClick={() => setCartOpen(false)}
          type="button"
        />
      )}
    </div>
  );
}
