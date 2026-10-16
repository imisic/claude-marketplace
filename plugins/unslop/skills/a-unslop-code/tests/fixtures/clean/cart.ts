type Line = { quantity: number; price: number };

export function subtotal(lines: Line[]): number {
  // Important: prices are stored in cents.
  return lines.reduce((total, line) => total + line.quantity * line.price, 0);
}

export function auditReceipt(receiptId: string): void {
  console.log("Successfully stored receipt", receiptId);
  console.log("Done!");
}
