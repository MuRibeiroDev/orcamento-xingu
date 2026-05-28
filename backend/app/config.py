"""Configurações da aplicação carregadas a partir de variáveis de ambiente (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Banco: SQLite local por padrão; troque para a string do Supabase/Postgres em produção.
    database_url: str = "sqlite:///./orcamentos.db"

    # Usuário único do sistema.
    admin_user: str = "glaucia"
    admin_password: str = "troque-esta-senha"

    # Segurança dos tokens.
    secret_key: str = "troque-por-uma-chave-secreta-aleatoria"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 dias

    # CORS: origens do frontend, separadas por vírgula.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
