import { Icon } from "../../components/ui/Icon.jsx";
import { formatCurrency, toMinorUnits } from "../../utils/currency.js";

export function CartPanel({
  cart,
  isOpen,
  onClose,
  onQuantityChange,
  onPlaceOrder,
  isSubmitting,
  orderError,
}) {
  const itemCount = cart.reduce((total, item) => total + item.quantity, 0);
  const subtotalCents = cart.reduce(
    (total, item) => total + toMinorUnits(item.price) * item.quantity,
    0,
  );

  return (
    <aside
      aria-label="Shopping bag"
      aria-modal="true"
      className={`cart-panel${isOpen ? " is-open" : ""}`}
      role="dialog"
      aria-hidden={!isOpen}
    >
      <div className="cart-panel-header">
        <div>
          <p className="eyebrow">YOUR EVERYDAY FINDS</p>
          <h2>Your bag <span>({itemCount})</span></h2>
        </div>
        <button className="icon-button" onClick={onClose} type="button" aria-label="Close bag">
          <Icon name="close" />
        </button>
      </div>

      {cart.length === 0 ? (
        <div className="cart-empty">
          <span className="cart-empty-icon"><Icon name="bag" /></span>
          <h3>A little room for good things.</h3>
          <p>Your bag is taking a breather. Add something lovely to get started.</p>
          <button className="button button-dark" onClick={onClose} type="button">
            Keep exploring <Icon name="arrowRight" />
          </button>
        </div>
      ) : (
        <>
          <div className="cart-items">
            {cart.map((item) => (
              <article className="cart-item" key={item.id}>
                <div className="cart-item-visual">
                  {item.image_url ? (
                    <img alt="" loading="lazy" src={item.image_url} />
                  ) : (
                    <span className="image-placeholder">No image</span>
                  )}
                </div>
                <div className="cart-item-details">
                  <span className="product-category">{item.category}</span>
                  <h3>{item.name}</h3>
                  <span className="cart-item-price">
                    {formatCurrency(item.price)}
                  </span>
                  <div className="quantity-control" aria-label={`Quantity for ${item.name}`}>
                    <button
                      aria-label={`Decrease ${item.name} quantity`}
                      onClick={() => onQuantityChange(item.id, item.quantity - 1)}
                      type="button"
                    >
                      <Icon name="minus" />
                    </button>
                    <span>{item.quantity}</span>
                    <button
                      aria-label={`Increase ${item.name} quantity`}
                      onClick={() => onQuantityChange(item.id, item.quantity + 1)}
                      disabled={item.quantity >= item.stock_quantity}
                      type="button"
                    >
                      <Icon name="plus" />
                    </button>
                  </div>
                  <button
                    className="cart-remove-button"
                    onClick={() => onQuantityChange(item.id, 0)}
                    type="button"
                  >
                    Remove
                  </button>
                </div>
              </article>
            ))}
          </div>
          <div className="cart-summary">
            <div className="cart-subtotal">
              <span>Estimated total</span>
              <strong>{formatCurrency(subtotalCents / 100)}</strong>
            </div>
            <p>The server confirms prices and stock when you place the order.</p>
            {orderError && (
              <p className="order-error" role="alert">{orderError}</p>
            )}
            <button
              className="button button-dark checkout-button"
              type="button"
              disabled={isSubmitting}
              onClick={onPlaceOrder}
            >
              {isSubmitting ? "Placing order…" : "Place order"}
            </button>
            <p className="cart-demo-note">
              No account or payment details are collected.
            </p>
          </div>
        </>
      )}
    </aside>
  );
}
