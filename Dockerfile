#FROM maven:3.9-eclipse-temurin-17 AS build
FROM registry.access.redhat.com/ubi8/openjdk-17:1.23-3.1764066423 AS builder
 
RUN mkdir project
WORKDIR /home/jboss/project

COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

#FROM eclipse-temurin:17-jre-alpine
FROM registry.access.redhat.com/ubi8/openjdk-17-runtime:1.23-3.1764066412
  
# Create directory for heap dumps
RUN mkdir -p /dumps && chmod 777 /dumps

# Copy the jar file
COPY --from=builder /home/jboss/project/target/memory-leak-demo-1.0.0.jar app.jar

# Set JVM options for heap dump on OOM
ENV JAVA_OPTS="-Xmx256m -Xms128m -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/dumps/heap_dump.hprof -XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:/dumps/gc.log"

EXPOSE 8080

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
