# Kafka microservices/CQRS study

This is a CQRS pattern study using kafka as a message broker. We'll be building
a movie review service with the follwing topology

rest client -> movie review rest api
                reads                 -> denormalized read-only data store (postgres)
                writes (user reviews) -> publish as kafka messages

review service
  - consumes messages from kafka
  - joins message data with (static) movie info
  - writes to read database