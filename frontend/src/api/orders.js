import { apiRequest } from "./client.js";

export function createOrder(items, options = {}) {
  return apiRequest(
    "/api/v1/orders",
    {
      ...options,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      body: JSON.stringify({
        items: items.map(({ product_id, quantity }) => ({
          product_id,
          quantity,
        })),
      }),
    },
  );
}
