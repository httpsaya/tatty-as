from decouple import config


ENV_POSSIBLE_OPTIONS = (
    "local",
    "prod",
)

ENV_ID = config("FINAL_PROJECT_ENV_ID", default = "local")
SECRET_KEY = config("FINAL_PROJECT_SECRET_KEY")