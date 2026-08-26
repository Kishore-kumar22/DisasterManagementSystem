
CREATE TABLE resources (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(120) NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	total_quantity INTEGER NOT NULL, 
	available_quantity INTEGER NOT NULL, 
	unit VARCHAR(40) NOT NULL, 
	location_name VARCHAR(160) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	full_name VARCHAR(120) NOT NULL, 
	email VARCHAR(160) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	`role` VARCHAR(20) NOT NULL, 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE audit_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER, 
	action VARCHAR(120) NOT NULL, 
	entity_type VARCHAR(80) NOT NULL, 
	entity_id INTEGER, 
	details TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE disasters (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	title VARCHAR(180) NOT NULL, 
	disaster_type VARCHAR(80) NOT NULL, 
	description TEXT NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	affected_population INTEGER NOT NULL, 
	latitude NUMERIC(10, 7) NOT NULL, 
	longitude NUMERIC(10, 7) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	reported_by INTEGER NOT NULL, 
	occurred_at DATETIME NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	severity_component FLOAT NOT NULL, 
	population_component FLOAT NOT NULL, 
	shortage_component FLOAT NOT NULL, 
	priority_score FLOAT NOT NULL, 
	priority_category VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(reported_by) REFERENCES users (id)
)

;


CREATE TABLE alerts (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	disaster_id INTEGER NOT NULL, 
	created_by INTEGER NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	message TEXT NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL, 
	expires_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(disaster_id) REFERENCES disasters (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)

;


CREATE TABLE disaster_status_history (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	disaster_id INTEGER NOT NULL, 
	changed_by INTEGER NOT NULL, 
	old_status VARCHAR(20), 
	new_status VARCHAR(20) NOT NULL, 
	changed_at DATETIME NOT NULL, 
	remarks TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(disaster_id) REFERENCES disasters (id), 
	FOREIGN KEY(changed_by) REFERENCES users (id)
)

;


CREATE TABLE responses (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	disaster_id INTEGER NOT NULL, 
	responder_id INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	assigned_at DATETIME NOT NULL, 
	started_at DATETIME, 
	completed_at DATETIME, 
	notes TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(disaster_id) REFERENCES disasters (id), 
	FOREIGN KEY(responder_id) REFERENCES users (id)
)

;


CREATE TABLE response_resources (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	response_id INTEGER NOT NULL, 
	resource_id INTEGER NOT NULL, 
	quantity_allocated INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_response_resource UNIQUE (response_id, resource_id), 
	FOREIGN KEY(response_id) REFERENCES responses (id), 
	FOREIGN KEY(resource_id) REFERENCES resources (id)
)

;

