Run with `docker-compose up --build`. Test with `./test.sh`.

Make requests like `curl localhost:5000/socket.io@latest/tree | jq`. The second request should be faster because of memcached.
