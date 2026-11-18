import { Icon } from "../ui/Icon.jsx";

export function Header({ cartCount, onCartClick }) {
  return (
    <header className="site-header page-width">
      <a className="brand" href="#" aria-label="Softspace home">
        <span className="brand-mark" aria-hidden="true">
          <span /><span /><span /><span />
        </span>
        <span>soft<span className="brand-light">space</span></span>
      </a>

      <nav className="main-nav" aria-label="Main navigation">
        <a className="nav-link is-current" href="#shop">Shop</a>
        <a className="nav-link" href="#shop">The everyday edit</a>
        <a className="nav-link" href="#about">Our approach</a>
      </nav>

      <button
        className="cart-button"
        type="button"
        onClick={onCartClick}
        aria-label={`Open shopping bag, ${cartCount} items`}
      >
        <Icon name="bag" />
        <span className="cart-button-label">Bag</span>
        <span className="cart-count">{cartCount}</span>
      </button>
    </header>
  );
}
