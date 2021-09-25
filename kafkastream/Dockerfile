FROM maven:3.8.2-openjdk-8 AS builder

COPY CryptoSightConverter/src /home/app/src
COPY CryptoSightConverter/pom.xml /home/app

RUN mvn -f /home/app/pom.xml clean package

FROM openjdk:8-jre-alpine

WORKDIR /converter

COPY --from=builder /home/app/target/CryptoSight-Converter.jar .

CMD ["java", "-jar", "CryptoSight-Converter.jar"]
