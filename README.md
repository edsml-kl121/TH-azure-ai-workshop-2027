### LAB 0

Please locate the `LAB_0_setup` folder. Then inside the `deploy.sh` file rename the resource group in line 25 e.g. mew3-azure-ai-workshop-rg to a name you prefer. Then, run the `deploy.sh` script

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

### LAB 1
Please go into `LAB_1_basic_agent/entra_id` folder and run

```
python azure_ai_basic.py
```

```
azure_ai_chat.py
```

### LAB 2
Please go into `LAB_2_AI_search/01_rag_agents/entra_id` folder and run
```
azure_ai_with_search_context_semantic.py
```

As a bonus for Agentic retrieval please go into `bonus_agentic_retrieval`.
Head into `indexing` then run the files inside `01_minimal` order e.g. `01_...`, `02_....`. Repeat the same for `02_medium`

For better visualization take a look at: https://azure-ai-search-knowledge-retrieval.vercel.app/test

### LAB 3
Inside `BE/deploy_to_azure.sh` configure RESOURCE_GROUP="mew3-azure-ai-workshop-rg" to align with the resource group name you prefer.
then inside the `BE/` folder run,
```
bash deploy-to-azure.sh
```

While waiting,
Please try out
```
python example1.py
```
Then once the container apps have successfully provisioned, please copy the deployed URL and replace this inside `BE/openapi.json`.

![alt text](image-1.png)

A) Go into API management instance inside the API Tab, upload your `openapi.json` specification. Tick subscription required.

B) Go into products tab. Please create a product using the recently registered API. Publish it.

C) Create an MCP server from the MCP server tab and assign the created product

![alt text](image-2.png)

D) Update the environment variables with the corresponding Key values, then please try out
```
python example2.py
```


### LAB 4
```
python sample_analyze_layout.py
```

### LAB 5

Lab 1
```
python 01_sequential_agents.py
```
Lab 2
```
python 02_handoff_simple_dev_ui.py
```

For future learnings: https://github.com/microsoft/agent-framework/tree/main/python/samples/getting_started

