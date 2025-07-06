import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from dramatiq.middleware import CurrentMessage, Retries, TimeLimit
import redis
from ..settings import settings

# Setup Redis backend for results
redis_client = redis.Redis.from_url(settings.redis_url)
result_backend = RedisBackend(client=redis_client)

# Setup RabbitMQ broker
rabbitmq_broker = RabbitmqBroker(url=settings.rabbitmq_url)

# Add middleware
rabbitmq_broker.add_middleware(CurrentMessage())
rabbitmq_broker.add_middleware(Retries(max_retries=3))
rabbitmq_broker.add_middleware(TimeLimit(time_limit=300000))  # 5 minutes
rabbitmq_broker.add_middleware(Results(backend=result_backend))

# Set as default broker
dramatiq.set_broker(rabbitmq_broker)
