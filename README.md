
# Task Manager Backend

This repository contains the backend code for a task manager application.
The backend is built using Flask and SQLAlchemy, providing a robust API for managing tasks, projects, 
and user authentication.

## Description

The Task Manager application allows users to create and manage tasks and projects. 
Key features include:
* User registration and authentication
* Task creation, updating, and deletion
* Project creation, updating, and deletion
* Assigning tasks to users

## Features
### Completed
- User endpoints
    - User Registration
    - User Login
    - User Update

### In Progress
- Project Management
- Task Management
- Tagging System

## Installation

Follow these steps to set up and run the backend locally:
- Clone the repository:

  - `https://github.com/derrickmunyole/gotaskmanager`

  - `cd gotaskmanager`

- Create a virtual environment:

  - `python -m venv venv`

  - `source venv/bin/activate  # On Windows use venv\Scripts\activate`

- Install dependencies

  - `pip install -r requirements.txt`

- Set up the database:
  - Install postgres on your local system. 
    Configure database creds and create the database (gotaskmanager in this case)

  - `DATABASE_URL=postgresql://username:password@localhost/gotaskmanager`

- Run database migrations:

  - `flask db upgrade`

- Start the application

  - `flask run`

## Usage

Once the backend is running, you can interact with the API using tools like Postman or cURL. 
Here are some example endpoints:

* User registration:
- Register a new user
    - POST user/register
    - Request Body

    `
    {
        "username": "exampleuser",
        "email": "user@example.com",
        "password": "password123"
    }
    `

* User login
- Login a user
    - POST /api/user/login
    - Request Body
  
`
{
    "username": "exampleuser",
    "password": "password123"
}
`

* Update user information
- PUT user/update
- Request Body

`
{
  "username": "new_username",
  "email": "new_email",
  "password": "new_password"
}
`

## Contributing
Contributions are what make the open-source community such an amazing place to learn, inspire, and create. 
Any contributions you make are ***greatly appreciated***.
1. Fork the Project
2. Create your Feature Branch (***git checkout -b feature/AmazingFeature***)
3. Commit your Changes (***git commit -m 'Add some AmazingFeature'***)
4. Push to the Branch (***git push origin feature/AmazingFeature***)

## Contact
Derrick Munyole - derrickjust@outlook.com

LinkedIn - https://www.linkedin.com/in/derrick-munyole-a2038792/
