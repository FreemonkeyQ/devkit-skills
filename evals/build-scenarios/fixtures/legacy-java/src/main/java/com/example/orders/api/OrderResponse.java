package com.example.orders.api;

import java.time.Instant;

public record OrderResponse(
        Long id,
        String customerName,
        String status,
        Instant createdAt,
        int itemCount) {
}
