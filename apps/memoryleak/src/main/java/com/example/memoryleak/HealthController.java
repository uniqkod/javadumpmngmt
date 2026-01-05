package com.example.memoryleak;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
public class HealthController {

    @GetMapping("/")
    public Map<String, Object> home() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "running");
        response.put("message", "Memory Leak Demo Application");
        return response;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        Runtime runtime = Runtime.getRuntime();
        long usedMemory = runtime.totalMemory() - runtime.freeMemory();
        long maxMemory = runtime.maxMemory();
        
        Map<String, Object> response = new HashMap<>();
        response.put("status", "UP");
        response.put("usedMemoryMB", usedMemory / (1024 * 1024));
        response.put("maxMemoryMB", maxMemory / (1024 * 1024));
        response.put("usagePercent", String.format("%.2f", (usedMemory * 100.0 / maxMemory)));
        
        return response;
    }
}
