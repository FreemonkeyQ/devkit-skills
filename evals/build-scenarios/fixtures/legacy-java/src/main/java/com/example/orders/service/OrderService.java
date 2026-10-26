package com.example.orders.service;

import com.example.orders.api.OrderResponse;
import com.example.orders.api.PageResponse;
import com.example.orders.domain.Order;
import com.example.orders.domain.OrderStatus;
import com.example.orders.repository.OrderRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class OrderService {

    private final OrderRepository orders;

    public OrderService(OrderRepository orders) {
        this.orders = orders;
    }

    @Transactional(readOnly = true)
    public PageResponse<OrderResponse> list(OrderStatus status, int page, int size) {
        Page<Order> result = orders.findByStatus(
                status,
                PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt")));
        List<OrderResponse> rows = result.getContent().stream()
                .map(order -> new OrderResponse(
                        order.getId(),
                        order.getCustomerName(),
                        order.getStatus().name(),
                        order.getCreatedAt(),
                        order.getItems().size()))
                .toList();
        return new PageResponse<>(rows, result.getNumber(), result.getSize(), result.getTotalElements());
    }

    @Transactional(readOnly = true)
    public PageResponse<OrderResponse> searchSlow(OrderStatus status, int page, int size) {
        List<Order> found = orders.searchSlow(
                status == null ? null : status.name(), size, page * size);
        List<OrderResponse> rows = found.stream()
                .map(order -> new OrderResponse(
                        order.getId(),
                        order.getCustomerName(),
                        order.getStatus().name(),
                        order.getCreatedAt(),
                        order.getItems().size()))
                .toList();
        return new PageResponse<>(rows, page, size, -1);
    }
}
