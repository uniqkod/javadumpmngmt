package com.example.memoryleak;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class MemoryLeakApplication {

    public static void main(String[] args) {
        SpringApplication.run(MemoryLeakApplication.class, args);
    }
}
