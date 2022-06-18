-- create database MoviesAndTV;

-- use MoviesAndTV;


-- Entities

drop table if exists Film;
create table Film (
	film_id varchar(16) not null,
	title varchar(128) not null,
	film_type varchar(16) not null,
	release_year int not null,
	date_added date not null,
	rating varchar(8) not null,
	duration varchar(16) not null,
	film_desc varchar(1024),
	-- this is random for having a consistant set of featured films
	feature float not null,
	
	primary key (film_id)
);

drop table if exists User;
create table User (
	user_id_ varchar(96) not null,
	username varchar(20) not null,
	pass_hash varchar(96) not null,
	pass_salt varchar(96) not null,
	
	primary key (user_id_)
);

drop table if exists Sess;
create table Sess (
	sess_id varchar(96) not null,
	user_id_ varchar(96) not null,
	
	primary key (sess_id),
	foreign key (user_id_) references User(user_id_)
);

drop table if exists Comment;
create table Comment (
	comment_id varchar(96) not null,
	user_id_ varchar(96) not null,
	film_id varchar(16) not null,
	date_ date not null,
	body varchar(1024) not null,
	
	primary key (comment_id)
);


drop table if exists Directed;
create table Directed (
	film_id varchar(16) not null,
	person_name varchar(64) not null,
	
	primary key (film_id, person_name),
	foreign key (film_id) references Film(film_id)
);

drop table if exists Acted;
create table Acted (
	film_id varchar(16) not null,
	person_name varchar(64) not null,
	
	primary key (film_id, person_name),
	foreign key (film_id) references Film(film_id)
);

drop table if exists Produced;
create table Produced (
	film_id varchar(16) not null,
	country_name varchar(64) not null,
	
	primary key (film_id, country_name),
	foreign key (film_id) references Film(film_id)
);

drop table if exists Listed;
create table Listed (
	film_id varchar(16) not null,
	genre_name varchar(64) not null,
	
	primary key (film_id, genre_name),
	foreign key (film_id) references Film(film_id)
);
