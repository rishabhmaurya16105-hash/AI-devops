const formatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
});

export function toMinorUnits(amount) {
  return Math.round(Number(amount) * 100);
}

export function formatCurrency(amount) {
  return formatter.format(Number(amount));
}
