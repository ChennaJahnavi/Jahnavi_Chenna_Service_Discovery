# Testing (End-to-End)

This document contains screenshots demonstrating the end-to-end testing of the service registry, two service instances, and the client-based discovery + load balancing.

## Screenshots

### Health checks and discovery (registry + instances)

![Registry and services health + discover output](assets/Screenshot_2026-03-18_at_9.13.04_PM-dfc08d19-bf71-42c5-ba5a-d2515db73aeb.png)

### Negative test (unknown service returns 503)

![Client /call output showing different chosen instances](assets/Screenshot_2026-03-18_at_9.20.32_PM-ec043412-4f3a-475b-9712-ae8f15d7e593.png)

### Failure / resilience test (stop one instance, TTL expiry)

![Stopping service2 and registry count drops](assets/Screenshot_2026-03-18_at_9.18.20_PM-3eb06d05-8a47-49c5-b21d-bde011a09204.png)

### Registry heartbeats / runtime logs

![Docker compose logs with register + heartbeat](assets/Screenshot_2026-03-18_at_9.08.13_PM-f7557d35-f3f7-436c-ad28-c1a56d0278b4.png)

### Test client-based service discovery and Verify random load balancing

![Unknown service returns 503](assets/Screenshot_2026-03-18_at_9.13.57_PM-53be8a67-59ae-46b0-8bcf-6a723cfd7b9e.png)

