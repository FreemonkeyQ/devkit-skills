package com.example.orders.domain;

public enum OrderStatus {
    PAID("已支付"),
    SHIPPED("已发货"),
    CANCELLED("已取消");

    private final String label;

    OrderStatus(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }
}
