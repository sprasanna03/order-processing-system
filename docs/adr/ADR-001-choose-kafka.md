
ADR-001: Choose Kafka for Event Bus
Status
Accepted

Context
We need durable, scalable event streaming for order lifecycle events with at-least-once delivery and replay.

Decision
Use Apache Kafka.

Consequences
Ops complexity > simple queues

Scales via partitions; ordering per partition

Enables replay/analytics
