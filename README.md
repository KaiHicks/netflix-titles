# Netflix Titles -- CSCI 330 Final Project

The application is live [here](https://cs330-term-project-full-stack.herokuapp.com/). 

## About

This project was originally created for my database systems final project. For the project, we were instructed to construct a full stack web application that utilizes a [given dataset](https://www.kaggle.com/shivamb/netflix-shows?select=netflix_titles.csv). While we were allowed to work in teams, I completed this project alone. The backend was uses Flask, while the front end uses Bootstrap for styling. These were chosen due to my familiarity with the tools, and their ease of use for creating applications of this size. The database is powered by SQLite3, as was required for the assignment. 

This repository contains a simple film browser powered by [this dataset](https://www.kaggle.com/shivamb/netflix-shows?select=netflix_titles.csv). The dataset contains details of various movies and TV shows on Netflix. You can browse the film collection by title, release year, or featured. You can view more information about each film including the directors, actors, genres, and comments left by other users. You can click on any actor or director's name to view more films they contributed to. If you are logged in, you will also see a comment box on any film's page. Here, you can leave comments that are visible to everyone.

There is a registration/login system accessable from the top-right of every page. It shows 'Sign Up' when you are unauthenticated. When you authenticate yourself by registering for an account, or logging into one, it will then show a menu where you can logout, or click 'My Page' to visit your page. A user's page contains all the comments they made on the site. When viewing one of your own comments, you will have the ability to edit or delete it. 

This application supports all CRUD database operations:
 * C - Creating an account or comment
 * R - Viewing films and information about films
 * U - Editing a comment
 * D - Deleting a comment and logging out (logging out deletes your session from the Sess table)

## Running the application

### Installing dependencies 

First, you must install Pipenv with
```
pip3 install pipenv
```
Next, install all required packages using 
```
python3 -m pipenv install
```

### Fetching dataset

Download the Netflix Titles dataset [here](https://www.kaggle.com/shivamb/netflix-shows?select=netflix_titles.csv) and place `netflix_titles.csv` in the root project directory. 

### Running the server

To run the backend locally, do
```
python3 -m pipenv run start
```

### Running unit tests

To run unit tests, do
```
python3 -m pipenv run test
```
This can take a while, so you can also pass the `-n` flag to specify multiple workers to execute tests in parallel. For example, the following command will spawn eight processes:
```
python3 -m pipenv run test -n 8
```

To check the test coverage, first make sure to run unit tests with one worker. Then, run 
```
python3 -m pipenv run coverage
```
To generate an HTML report, use 
```
python3 -m pipenv run coverage-html
```