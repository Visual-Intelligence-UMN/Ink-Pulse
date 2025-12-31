CREATE TABLE `json_table` (
	`id` text NOT NULL,
	`group` text NOT NULL,
	`content` text NOT NULL,
	PRIMARY KEY(`id`, `group`)
);
--> statement-breakpoint
CREATE TABLE `segment_table` (
	`id` text NOT NULL,
	`group` text NOT NULL,
	`content` text NOT NULL,
	PRIMARY KEY(`id`, `group`)
);
