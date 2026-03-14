-- Executes on container bootstrap using MYSQL_DATABASE from environment.
CREATE TABLE IF NOT EXISTS bootstrap_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    initialized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO bootstrap_status () VALUES ();