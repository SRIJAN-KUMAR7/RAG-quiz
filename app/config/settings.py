from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./quiz.db"

    # Gemini API
    gemini_api_key: str

    # Pinecone
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str
    pinecone_dimension: int

    # File storage
    upload_dir: str = "./uploads"
    max_file_size: int = 10_485_760

    # Chunking
    chunk_size: int = 800
    chunk_overlap: int = 200

    # Question generation
    default_question_count: int = 10
    max_question_count: int = 50

    # Grading thresholds
    mcq_passing_score: int = 70
    descriptive_passing_score: int = 60

    # Security
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # Redis / Celery
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    # Logging
    log_level: str = "INFO"

    # Environment
    environment: str = "development"
    debug: bool = True

    class Config:
        env_file = ".env"     # load from your .env file
        extra = "ignore"      # ignore unknown env variables

# create the singleton instance
settings = Settings()
