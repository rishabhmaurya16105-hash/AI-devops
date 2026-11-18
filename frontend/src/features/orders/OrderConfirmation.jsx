import { formatCurrency } from "../../utils/currency.js";

export function OrderConfirmation({ order, onClose }) {
  if (!order) {
    return null;
  }

  return (
    <div className="order-confirmation-backdrop">
      <section
        aria-labelledby="order-confirmation-title"
        aria-modal="true"
        className="order-confirmation"
        role="dialog"
      >
        <span className="order-confirmation-mark" aria-hidden="true">✓</span>
        <p className="eyebrow">ORDER PLACED</p>
        <h2 id="order-confirmation-title">Thank you!</h2>
        <p>Your order has been created successfully.</p>
        <dl className="order-confirmation-details">
          <div>
            <dt>Order number</dt>
            <dd>{order.order_number}</dd>
          </div>
          <div>
            <dt>Confirmed total</dt>
            <dd>{formatCurrency(order.total_amount)}</dd>
          </div>
        </dl>
        <p className="order-auth-note">
          This local demo order is not associated with a signed-in account.
        </p>
        <button className="button button-dark" onClick={onClose} type="button">
          Continue browsing
        </button>
      </section>
    </div>
  );
}
