import { Icon } from "../../components/ui/Icon.jsx";
import { formatCurrency } from "../../utils/currency.js";

export function ProductCard({ product, onAdd }) {
  const isOutOfStock = product.stock_quantity < 1;

  return (
    <article className="product-card">
      <div className="product-visual">
        {product.is_sample && <span className="product-badge">SAMPLE</span>}
        {product.image_url ? (
          <img
            alt={product.name}
            className="product-image"
            loading="lazy"
            src={product.image_url}
          />
        ) : (
          <span className="image-placeholder">Image not available</span>
        )}
        <button
          aria-label={
            isOutOfStock
              ? `${product.name} is out of stock`
              : `Add ${product.name} to bag`
          }
          className="quick-add"
          onClick={onAdd}
          disabled={isOutOfStock}
          type="button"
        >
          {isOutOfStock ? "—" : <Icon name="plus" />}
        </button>
      </div>
      <div className="product-info">
        <div>
          <span className="product-category">{product.category}</span>
          <h3>{product.name}</h3>
          <p>{product.description}</p>
          {isOutOfStock && <span className="stock-status">Out of stock</span>}
        </div>
        <span className="product-price">{formatCurrency(product.price)}</span>
      </div>
    </article>
  );
}
