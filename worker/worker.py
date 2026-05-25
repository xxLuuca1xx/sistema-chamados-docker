import redis
import os

print("Iniciando Worker de Notificações...", flush=True)

r = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), decode_responses=True)
pubsub = r.pubsub()
pubsub.subscribe('novos_chamados')

print("Aguardando novos chamados...", flush=True)

for message in pubsub.listen():
    if message['type'] == 'message':
        dado = message['data']
        print(f"[WORKER] -> Enviando notificação: {dado}", flush=True)