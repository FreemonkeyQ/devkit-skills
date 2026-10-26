package com.example.orders.repository;

import com.example.orders.domain.Order;
import com.example.orders.domain.OrderStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface OrderRepository extends JpaRepository<Order, Long> {

    Page<Order> findByStatus(OrderStatus status, Pageable pageable);

    @Query(value = """
            SELECT * FROM orders
            WHERE (:status IS NULL OR status = :status)
            ORDER BY created_at DESC
            LIMIT :size OFFSET :offset
            """, nativeQuery = true)
    List<Order> searchSlow(@Param("status") String status,
                           @Param("size") int size,
                           @Param("offset") int offset);
}
