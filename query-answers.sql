-- 1. When are all the listed movies released?

-- Input for a histogram
select release_year, count(*) as num_films
from Film
where film_type="Movie"
group by release_year
order by release_year desc;

-- Top five years
select release_year, count(*) as num_films
from Film
where film_type="Movie"
group by release_year
order by num_films desc
limit 5;

-- 2. When are all the listed TV series released?

-- Input for a histogram
select release_year, count(*) as num_films
from Film
where film_type="TV Show"
group by release_year
order by release_year desc;

-- Top five years
select release_year, count(*) as num_films
from Film
where film_type="TV Show"
group by release_year
order by num_films desc
limit 5;

-- 3. Where are all the listed movies/TV series produced?

select country_name, count(*) as num_films
from Film natural join Produced
group by country_name
order by num_films desc;

-- TV Shows
select country_name, count(*) as num_films
from Film natural join Produced
where film_type="TV Show"
group by country_name
order by num_films desc;

-- Movies
select country_name, count(*) as num_films
from Film natural join Produced
where film_type="Movie"
group by country_name
order by num_films desc;

-- 4. Are the ratings of all the movies added in the last three years (2019-2021) different from the ratings of all movies added prior to 2019? If so, what is the difference?

-- Aired on tv

-- Before 2019
select 
	rating,
	100.0*count(*)/(
			select count(*)
			from Film 
			where release_year < 2019 and rating in 
				("TV-MA", "TV-14", "TV-PG", "TV-G", "TV-Y7-FV", "TV-Y7", 
				"TV-Y")
		) 
		as percent_films
from Film
where release_year < 2019 and rating in 
	("TV-MA", "TV-14", "TV-PG", "TV-G", "TV-Y7-FV", "TV-Y7", "TV-Y")
group by rating
order by case
	when rating="TV-MA"       then 1
	when rating="TV-14"       then 2
	when rating="TV-PG"       then 3
	when rating="TV-G"        then 4
	when rating="TV-Y7-FV"    then 5
	when rating="TV-Y7"       then 6
	when rating="TV-Y"        then 7
	else 8
	end;

-- After 2019
select 
	rating,
	100.0*count(*)/(
			select count(*)
			from Film 
			where release_year >= 2019 and rating in 
				("TV-MA", "TV-14", "TV-PG", "TV-G", "TV-Y7-FV", "TV-Y7", 
				"TV-Y")
		) 
		as percent_films
from Film
where release_year >= 2019 and rating in 
	("TV-MA", "TV-14", "TV-PG", "TV-G", "TV-Y7-FV", "TV-Y7", "TV-Y")
group by rating
order by case
	when rating="TV-MA"       then 1
	when rating="TV-14"       then 2
	when rating="TV-PG"       then 3
	when rating="TV-G"        then 4
	when rating="TV-Y7-FV"    then 5
	when rating="TV-Y7"       then 6
	when rating="TV-Y"        then 7
	else 8
	end;

-- Aired in theaters

-- Before 2019
select 
	rating,
	100.0*count(*)/(
			select count(*)
			from Film 
			where release_year < 2019 and rating not in 
				("TV-MA", "TV-14", "TV-PG", "TV-G", "TV-Y7-FV", "TV-Y7", 
				"TV-Y")
		) 
		as percent_films
from Film
where release_year < 2019 and rating not in 
	("TV-MA", "TV-14", "TV-PG", "TV-G", "TV-Y7-FV", "TV-Y7", "TV-Y")
group by rating
order by case
	when rating="NC-17" then 1
	when rating="R"     then 2
	when rating="PG-13" then 3
	when rating="PG"    then 4
	when rating="G"     then 5
	else 6
	end;

-- After 2019
select 
	rating,
	100.0*count(*)/(
			select count(*)
			from Film 
			where release_year >= 2019 and rating not in 
				("TV-MA", "TV-14", "TV-PG", "TV-G", "TV-Y7-FV", "TV-Y7", 
				"TV-Y")
		) 
		as percent_films
from Film
where release_year >= 2019 and rating not in 
	("TV-MA", "TV-14", "TV-PG", "TV-G", "TV-Y7-FV", "TV-Y7", "TV-Y")
group by rating
order by case
	when rating="NC-17" then 1
	when rating="R"     then 2
	when rating="PG-13" then 3
	when rating="PG"    then 4
	when rating="G"     then 5
	else 6
	end;