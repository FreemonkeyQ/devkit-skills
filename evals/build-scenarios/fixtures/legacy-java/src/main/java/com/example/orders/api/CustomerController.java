package com.example.orders.api;

import com.example.orders.export.CustomerExportService;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/customers")
public class CustomerController {

    private final CustomerExportService service;

    public CustomerController(CustomerExportService service) {
        this.service = service;
    }

    @GetMapping("/export")
    public ResponseEntity<byte[]> export() {
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=customers.csv")
                .body(service.export());
    }
}
