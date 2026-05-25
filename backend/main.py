from fastapi import FastAPI, HTTPException
import psycopg2
import redis
import os
from prometheus_client import make_asgi_app, Counter

app = FastAPI()

# Métricas
REQUESTS = Counter('chamados_criados_total', 'Total de chamados abertos')
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Conexões
db_conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host="db"
)
redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))

with db_conn.cursor() as cur:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chamados (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(100),
            descricao TEXT,
            status VARCHAR(20) DEFAULT 'Aberto'
        )
    """)
    db_conn.commit()

@app.post("/chamados/")
def criar_chamado(titulo: str, descricao: str):
    try:
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chamados (titulo, descricao) VALUES (%s, %s) RETURNING id;",
                (titulo, descricao)
            )
            chamado_id = cur.fetchone()[0]
            db_conn.commit()
        
        redis_client.publish('novos_chamados', f"Chamado #{chamado_id}: {titulo}")
        REQUESTS.inc() 
        
        return {"id": chamado_id, "mensagem": "Chamado aberto com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))