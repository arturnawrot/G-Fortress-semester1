# G-Fortress-semester1

Run for development

```bash
docker-compose up -d
./run.sh npm run dev
```

Tests

```bash
./run.sh test
```

 - Frontend Endpoints:

   - http://127.0.0.1:5173/login

   - http://127.0.0.1:5173/dashboard

 - Backend Endpoints
   - http://127.0.0.1:8000/docs - endpoint documentation, Swagger UI ("try it out" option)

   - http://127.0.0.1:8000/ - returns status of the API. 200 if everything is ok and accessible, otherwise there is an error

   - http://127.0.0.1:8000/api/users/me - returns the username of the currently authenticated user

   - http://127.0.0.1:8000/api/users/protected-data - sample protected message that is supposed to be encrypted with AES-256. See `test_full_secure_aes_workflow` test at `backend/test_main.py` to see an example of AES-256 encrypted communication between the client and the server.

 - For scheduling scans `celery` and `redis` are used. See docker-compose.yml

 - Database: neo4j

 - See `nltm_windows_agent` directory to understand how will the application retrieve NTLM hashes. An API for the agent that will allow the communication with the backend to be implemented soon...
