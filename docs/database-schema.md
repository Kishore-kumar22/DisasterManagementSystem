# Database schema reference

| Table | Key relationships |
|---|---|
| `users` | One user reports many disasters, creates alerts, changes status history, and can be assigned many responses |
| `disasters` | Belongs to a reporting user; has many responses, alerts, and status-history records |
| `resources` | Has many allocation rows; total and available quantities are constrained by application validation |
| `responses` | Belongs to one disaster and one responder; has many response-resource allocations |
| `response_resources` | Joins responses and resources; stores quantity allocated and prevents duplicate response/resource pairs |
| `alerts` | Belongs to one disaster and one creator |
| `disaster_status_history` | Belongs to one disaster and the user who made the change |
| `audit_logs` | Optionally references the acting user and stores an action description |

Important indexes are present on incident type, severity, status, priority category, occurrence time, response disaster/responder identifiers, resource category/status, and alert status. These support the filtering and dashboard queries used by the prototype.

## Quantity rule

For every resource, `0 <= available_quantity <= total_quantity`. A resource allocation is accepted only when the requested positive quantity is less than or equal to the current available quantity. The route decreases `available_quantity` in the same database transaction as the allocation record.

## Status values

Disaster statuses are `Reported`, `Responding`, and `Resolved`. Response statuses are `Assigned`, `In Progress`, and `Completed`. Resource statuses are synchronized to `Available`, `Low Stock`, or `Depleted` based on remaining quantity.
