package com.example.orders.export;

import org.springframework.stereotype.Component;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.util.List;

@Component
public class CsvExportWriter {

    public void write(OutputStream out, List<String> headers, List<List<String>> rows) throws IOException {
        BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(out, StandardCharsets.UTF_8));
        writer.write(String.join(",", headers));
        writer.newLine();
        for (List<String> row : rows) {
            writer.write(String.join(",", row));
            writer.newLine();
        }
        writer.flush();
    }
}
