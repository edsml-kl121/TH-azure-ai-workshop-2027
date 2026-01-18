### LAB 0

Please locate the `LAB_0_setup` folder. Then run the `deploy.sh` script

```
bash deploy.sh
```

Meanwhile, please locate to the root directory and create a virtual environment via.
```
python -m venv venv
```
Then activate the environment
```
source venv/bin/activate
```

After waiting for 15 minutes, all the resource should be created. Please check the `.env` file to see if all environmental variables have been generated.

Please locate to azure portal and set API Access control to 'both' 

![alt text](image.png).

Then locate to the `scripts/` folder and run

```
python hydrating_vector_index.py
```
Then test the ingested result:
```
python query_search_index.py
```

You should now see the result and the setup for vector database is ready.


https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started