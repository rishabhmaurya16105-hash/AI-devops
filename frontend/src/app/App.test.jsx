import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createOrder } from "../api/orders.js";
import { getProducts } from "../api/products.js";
import App from "./App.jsx";

vi.mock("../api/products.js", () => ({ getProducts: vi.fn() }));
vi.mock("../api/orders.js", () => ({ createOrder: vi.fn() }));

const product = {
  id: 1,
  slug: "test-notebook",
  name: "Test Notebook",
  description: "A notebook for frontend tests.",
  price: "18.25",
  image_url: null,
  category: "Workspace",
  stock_quantity: 5,
  is_sample: true,
};

const createdOrder = {
  order_number: "ORD-TEST-123",
  total_amount: "18.25",
};

async function addProductToCart(user) {
  await user.click(
    await screen.findByRole("button", { name: "Add Test Notebook to bag" }),
  );
}

async function openCart(user) {
  await user.click(
    screen.getByRole("button", { name: "Open shopping bag, 1 items" }),
  );
  return screen.getByRole("dialog", { name: "Shopping bag" });
}

describe("DevOpsMart storefront", () => {
  beforeEach(() => {
    getProducts.mockReset().mockResolvedValue([product]);
    createOrder.mockReset().mockResolvedValue(createdOrder);
  });

  it("shows a loading state while the product API is pending", async () => {
    let resolveProducts;
    getProducts.mockReturnValue(
      new Promise((resolve) => {
        resolveProducts = resolve;
      }),
    );

    render(<App />);

    expect(screen.getByRole("status")).toHaveTextContent("Loading products…");
    resolveProducts([product]);
    expect(await screen.findByRole("heading", { name: "Test Notebook" }))
      .toBeInTheDocument();
  });

  it("loads and displays products from the API", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Test Notebook" }))
      .toBeInTheDocument();
    expect(screen.getByText("A notebook for frontend tests."))
      .toBeInTheDocument();
    expect(getProducts).toHaveBeenCalledOnce();
  });

  it("shows a clear empty state when the catalog has no products", async () => {
    getProducts.mockResolvedValueOnce([]);

    render(<App />);

    expect(await screen.findByRole("heading", { name: "No products yet" }))
      .toBeInTheDocument();
  });

  it("shows an API error and retries product loading", async () => {
    const user = userEvent.setup();
    getProducts
      .mockRejectedValueOnce(new Error("API unavailable"))
      .mockResolvedValueOnce([product]);

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "We couldn't load the product collection.",
    );
    await user.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByRole("heading", { name: "Test Notebook" }))
      .toBeInTheDocument();
    expect(getProducts).toHaveBeenCalledTimes(2);
  });

  it("adds a product, updates its quantity, and removes it from the cart", async () => {
    const user = userEvent.setup();
    render(<App />);
    await addProductToCart(user);

    const cart = await openCart(user);
    const quantity = within(cart).getByLabelText(
      "Quantity for Test Notebook",
    );

    expect(quantity).toHaveTextContent("1");
    await user.click(
      within(cart).getByRole("button", {
        name: "Increase Test Notebook quantity",
      }),
    );
    expect(quantity).toHaveTextContent("2");

    await user.click(
      within(cart).getByRole("button", {
        name: "Decrease Test Notebook quantity",
      }),
    );
    expect(quantity).toHaveTextContent("1");

    await user.click(within(cart).getByRole("button", { name: "Remove" }));
    expect(
      await within(cart).findByText("A little room for good things."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Open shopping bag, 0 items" }),
    ).toBeInTheDocument();
  });

  it("places an order and clears the cart only after success", async () => {
    const user = userEvent.setup();
    render(<App />);
    await addProductToCart(user);
    await openCart(user);

    await user.click(screen.getByRole("button", { name: "Place order" }));

    expect(
      await screen.findByRole("heading", { name: "Thank you!" }),
    ).toBeInTheDocument();
    expect(screen.getByText("ORD-TEST-123")).toBeInTheDocument();
    expect(createOrder).toHaveBeenCalledWith([
      { product_id: 1, quantity: 1 },
    ]);
    expect(
      screen.getByRole("button", { name: "Open shopping bag, 0 items" }),
    ).toBeInTheDocument();
  });

  it("keeps the cart contents when order placement fails", async () => {
    const user = userEvent.setup();
    createOrder.mockRejectedValueOnce(new Error("Stock changed; try again."));
    render(<App />);
    await addProductToCart(user);
    const cart = await openCart(user);

    await user.click(within(cart).getByRole("button", { name: "Place order" }));

    expect(await within(cart).findByRole("alert")).toHaveTextContent(
      "Stock changed; try again.",
    );
    expect(within(cart).getByRole("heading", { name: "Test Notebook" }))
      .toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Open shopping bag, 1 items" }),
    ).toBeInTheDocument();
    expect(
      within(cart).getByLabelText("Quantity for Test Notebook"),
    ).toHaveTextContent("1");
  });
});
