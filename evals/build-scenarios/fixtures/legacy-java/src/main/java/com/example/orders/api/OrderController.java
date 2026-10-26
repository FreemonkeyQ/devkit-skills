package com.example.orders.api;

import com.example.orders.domain.OrderStatus;
import com.example.orders.service.OrderService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/orders")
public class OrderController {

    private final OrderService service;

    public OrderController(OrderService service) {
        this.service = service;
    }

    @GetMapping
    public PageResponse<OrderResponse> list(
            @RequestParam(defaultValue = "PAID") OrderStatus status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return service.list(status, page, size);
    }

    @GetMapping("/search")
    public PageResponse<OrderResponse> search(
            @RequestParam(required = false) OrderStatus status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return service.searchSlow(status, page, size);
    }
}
