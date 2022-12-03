"""
Main module. Contains lot of thing, including endpoint of the api and everything to authenticate
"""
import json
from datetime import datetime, timedelta
from typing import Any, Optional

import requests
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from pydantic import BaseModel  # pylint: disable=E0611
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from database import database
from database.database import oauth2_scheme, pwd_context
from exceptions import StargazerException

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class NewJsonResponse(JSONResponse):
    """
    Response Class for Fastapi.
    """

    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=True,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


# Define app
app = FastAPI(
    title="Stargazer",
    redoc_url="/redoc",
    docs_url="/docs",
    openapi_url="/openapi.json",
    default_response_class=NewJsonResponse,
)


@app.exception_handler(StargazerException)
async def exception_handler(
    request: Request, exc: StargazerException
):  # pylint: disable=W0613
    """
    Exception handler to return properly in case of any exception
    Return Exception instead of HTTPError
    :param request: request Executed
    :type request: fastapi Request
    :param exc: exception raised
    :type exc: Exception
    :return NewJsonResponse -> fastapi Response
    rtype: NewJsonResponse
    """
    return NewJsonResponse(status_code=400, content={"message": exc.message})


# Authentication
# --------------
class Token(BaseModel):  # pylint: disable=R0903
    """Token"""

    access_token: str
    token_type: str


class TokenData(BaseModel):  # pylint: disable=R0903
    """TokenData"""

    username: Optional[str] = None


@app.on_event("startup")
async def start_db():
    """
    wait for db to start
    :return: None
    """
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)


def verify_password(plain_password, hashed_password):
    """
    Check pwd, if match with the encrypted pwd in db
    :param plain_password: pwd in plain text
    :param hashed_password: crypted pwd
    :return: True if pwd are matching else False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hash password
    :param password: pwd in plain text
    :return: hashed pwd
    """
    return pwd_context.hash(password)


async def get_user(
    db: AsyncSession, username: str  # pylint: disable=C0103
) -> database.User:
    """
    read from users table the user matching unique username
    :param db: db
    :param username: username
    :return: models.User
    """
    result = await db.execute(select(database.User).filter_by(username=username))
    return result.scalars().first()


async def authenticate_user(
    db: AsyncSession, username: str, password: str  # pylint: disable=C0103
) -> database.User:
    """
    Return User when asking for authenticator
    :param db: db
    :param username: username
    :param password: pwd
    :return: User if match, else False
    """
    user = await get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create Token if USer has been successfully authenticated
    :param data: data
    :param expires_delta: Time after token expires
    :return: token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ----------


# Can be improve (cartography of known repo ?)
def get_repo_into_starneighbours(fullname_repo, star_neighbours):
    """
    Check if a repo is already in neighbours. If yes, return the elem, else return False
    :param fullname_repo: repo name
    :param star_neighbours: complete list
    :return:
    """
    for repo in star_neighbours:
        if fullname_repo == repo.get("repo"):
            return repo
    return False


def get_from_github(endpoint, user: "", repo="") -> json:
    """
    Abstract github api calls in this func
    :param endpoint: endpoint to call
    :param user: Optionnal if endpoint contains any user
    :param repo: Optionnal if endpoint contains any repo
    :return: requests.Response with github return, or Exception
    """
    try:
        if endpoint == "stargazer":
            url = f"https://api.github.com/repos/{user}/{repo}/stargazers"
        if endpoint == "starred":
            url = f"https://api.github.com/users/{user}/starred"
        res = requests.get(url, timeout=60)
        if not res:
            raise StargazerException(
                message=f"Nothing found with user {user} and repo {repo}"
            )
        return res.json()
    except requests.ConnectionError as connexion_error:
        raise StargazerException(
            message=f"Connexion_error: {connexion_error}"
        ) from connexion_error


# Endpoints
# ---------


@app.post("/token", response_model=Token)
async def login_for_access_token(
    db: AsyncSession = Depends(database.get_db),  # pylint: disable=C0103
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Endpoint to authenticate user. Called when trying to authenticator an user.
    :param db: db
    :param form_data: form_data with credential asking
    :return: dict containing access token and type
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
async def root():
    """
    Main endppoint, redirect to /docs
    :return: redirectResponse to /docs
    """
    return RedirectResponse(url="/docs")


@app.get("/repos/{user}/{repo}/starneighbours")
async def get_starneighbours(
    user: str, repo: str, token: str = Depends(oauth2_scheme)
):  # pylint: disable=W0613
    """
    Endpoint to retrieve neighbours' repo.
    :param user: User's repo
    :param repo: repo name
    :param token: for authenticator
    :return: list of "neighbours repository"
    """
    starneighbours = []
    try:
        stargazers = get_from_github(endpoint="stargazer", user=user, repo=repo)
        if not stargazers:
            return "This project has no stargazer"
        for stargazer in stargazers:
            stargazer_login = stargazer.get("login")
            starred = get_from_github(endpoint="starred", user=stargazer_login)

            for project_starred in starred:
                fullname_project = project_starred.get("full_name")
                if fullname_project == f"{user}/{repo}":
                    continue
                project_in_starneighbours = get_repo_into_starneighbours(
                    fullname_project, starneighbours
                )
                if project_in_starneighbours:
                    project_in_starneighbours.get("stargazers").append(stargazer_login)
                else:
                    starneighbours.append(
                        {"repo": fullname_project, "stargazers": [stargazer_login]}
                    )
    except StargazerException as exc:
        raise exc
    if not starneighbours:
        return "This repo has no neighbours"
    return starneighbours


@app.get("/healthz")
async def healthz():
    """CHeck if api is running"""
    return "The api is running"


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
