import { apiRequest } from "./client.js";

export function getProducts(options = {}) {
  return apiRequest("/api/v1/products", options);
}
