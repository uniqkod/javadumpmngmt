FROM registry.access.redhat.com/ubi8/openjdk-17:1.23-3.1764066423 AS builder
 
RUN mkdir project
WORKDIR /home/jboss/project

COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

FROM registry.access.redhat.com/ubi8/openjdk-17-runtime:1.23-3.1764066412

# Copy the jar file
COPY --from=builder /home/jboss/project/target/mount-access-controller-1.0.0.jar app.jar

ENV JAVA_OPTS="-Xmx512m -Xms256m"

EXPOSE 8080

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
