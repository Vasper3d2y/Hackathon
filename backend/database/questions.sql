DROP TABLE IF EXISTS questions;

CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject VARCHAR(50) NOT NULL,
    question_text VARCHAR(500) NOT NULL,
    option_a VARCHAR(100) NOT NULL,
    option_b VARCHAR(100) NOT NULL,
    option_c VARCHAR(100) NOT NULL,
    option_d VARCHAR(100) NOT NULL,
    correct_index INT NOT NULL
);

INSERT INTO questions (subject, question_text, option_a, option_b, option_c, option_d, correct_index) VALUES
('C programming', 'Which header file is required to use the standard input/output functions like printf() and scanf()?', '<math.h>','<conio.h>', '<string.h>', '<stdio.h>', 3),
('C programming', 'Which of the following is the correct way to declare a pointer that points to an integer?', 'int &p;', 'int *p;', 'pointer p;', 'float p;', 1),
('C programming', 'What is the size of a char data type in C on most platforms?', '1 byte', '2 bytes', '4 bytes', '8 bytes', 0),
('C programming', 'Which bitwise operator is used to perform a bitwise NOT (inversion) operation in C?', '&', '|', '~', '^', 2),
('C programming', 'Which string function is used to copy one string into another in C?', 'strcmp()', 'strlen()', 'strcpy()', 'strcat()', 2),
('Web Hosting', 'Which of the following hosting types offers the highest control and performance?', 'Shared Hosting', 'VPS Hosting', 'Cloud Hosting', 'Dedicated Hosting', 3),
('Web Hosting', 'What happens if you forget to configure your DNS after uploading your site files to the server?', 'User will get a 403 Forbidden error', 'The server will deny requests from browsers', 'Visitors cannot reach your site using its domain name', 'Your site wont appear on search engines', 2),
('Web Hosting', 'Which protocol is primarily used for uploading files to a web hosting server?', 'SMTP', 'FTP', 'HTTP', 'POP3', 1),
('Web Hosting', 'Which of these best describes a Web server?', 'A type of web browser', 'A physical internet cable', 'A specialized computer', 'A digital domain name', 2),
('Web Hosting', 'Which hosting environment shares server resources (RAM, CPU, disk space) among multiple users, making it a cost-effective option?', 'Shared Hosting', 'VPS (Virtual Private Server) Hosting', 'Dedicated Hosting', 'Colocation Hosting', 0);
