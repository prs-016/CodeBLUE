Local Setup
===========

Environment
-----------

1. Copy ``.env.example`` to ``.env``.
2. Fill only the credentials you have. Blank blockchain credentials are acceptable for local UI and API development.

Docker
------

Start the default stack:

.. code-block:: bash

   docker compose up --build

Optional services:

.. code-block:: bash

   docker compose --profile data up data_pipeline
   docker compose --profile blockchain up blockchain_client

Direct development
------------------

Backend:

.. code-block:: bash

   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload

Frontend:

.. code-block:: bash

   cd frontend
   npm install
   npm run dev
