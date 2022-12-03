Stargazer
========================

This project enables you to check linked project by stargazer
---------------

Requirement: You need to have Python install on your machine

Once this project is cloned, first create a virtual environment using:
 > python -m venv <venv-name>

 > <venv-name>\Scripts\activate

Then, you have to install the project and all it's dependency:
 > pip install -r .\requirements.txt


You have inside the project a file for a little database:
 > database.sqlite3

To run this Api in local, launch in a shell:
 > cd stargazer

 > uvicorn main:app --port 8000