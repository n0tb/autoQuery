FROM redis:5.0-alpine

COPY redis_db ./
COPY redis.conf /usr/local/etc/redis/redis.conf
RUN cat redis_db|redis-cli -n 1