<?php

$items = $lineItems ?? [];

final class Invoice
{
    public function __construct(private int $net, private int $tax) {}

    public function total(): int
    {
        // Note: both amounts use the same currency.
        return $this->net + $this->tax;
    }
}
