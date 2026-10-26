package com.example.orders.service;

import com.example.orders.api.OrderResponse;
import com.example.orders.api.PageResponse;
import com.example.orders.domain.Order;
import com.example.orders.domain.OrderStatus;
import com.example.orders.repository.OrderRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;

import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    OrderRepository orders;

    @InjectMocks
    OrderService service;

    @Test
    void listMapsPage() {
        Order order = new Order();
        order.setId(1L);
        order.setCustomerName("Acme");
        order.setStatus(OrderStatus.PAID);
        order.setCreatedAt(Instant.parse("2026-10-01T08:00:00Z"));
        order.setItems(List.of());
        when(orders.findByStatus(eq(OrderStatus.PAID), any(PageRequest.class)))
                .thenReturn(new PageImpl<>(List.of(order)));

        PageResponse<OrderResponse> result = service.list(OrderStatus.PAID, 0, 20);

        assertThat(result.items()).hasSize(1);
        assertThat(result.items().get(0).itemCount()).isZero();
    }
}
