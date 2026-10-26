package com.example.orders.export;

import com.example.orders.domain.Customer;
import com.example.orders.repository.CustomerRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.List;

@Service
public class CustomerExportService {

    private final CustomerRepository customers;
    private final CsvExportWriter writer;

    public CustomerExportService(CustomerRepository customers, CsvExportWriter writer) {
        this.customers = customers;
        this.writer = writer;
    }

    @Transactional(readOnly = true)
    public byte[] export() {
        List<List<String>> rows = customers.findAll().stream()
                .map(this::toRow)
                .toList();
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try {
            writer.write(out, List.of("id", "name", "email"), rows);
        } catch (IOException e) {
            throw new IllegalStateException("cannot export customers", e);
        }
        return out.toByteArray();
    }

    private List<String> toRow(Customer customer) {
        return List.of(String.valueOf(customer.getId()), customer.getName(), customer.getEmail());
    }
}
