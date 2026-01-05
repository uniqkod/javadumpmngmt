package com.example.memoryleak;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

@Service
public class MemoryLeakService {

    private static final List<byte[]> memoryLeakList = new ArrayList<>();
    private static final Random random = new Random();
    private int iteration = 0;

    @Scheduled(fixedRate = 5000) // Every 5 seconds
    public void leakMemory() {
        iteration++;
        
        // Allocate 10MB of memory each time
        int size = 10 * 1024 * 1024; // 10 MB
        byte[] leak = new byte[size];
        
        // Fill with random data to prevent JVM optimizations
        random.nextBytes(leak);
        
        // Add to static list (never gets garbage collected)
        memoryLeakList.add(leak);
        
        long usedMemoryMB = (Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()) / (1024 * 1024);
        long maxMemoryMB = Runtime.getRuntime().maxMemory() / (1024 * 1024);
        
        System.out.println(String.format(
            "Iteration %d: Leaked %d MB | Used Memory: %d MB / %d MB (%.2f%%)",
            iteration,
            (iteration * 10),
            usedMemoryMB,
            maxMemoryMB,
            (usedMemoryMB * 100.0 / maxMemoryMB)
        ));
    }
}
