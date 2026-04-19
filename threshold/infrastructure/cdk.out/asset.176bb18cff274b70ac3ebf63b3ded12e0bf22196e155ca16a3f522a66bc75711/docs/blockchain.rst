Blockchain Scaffold
===================

The blockchain module is designed for pragmatic hackathon development:

- ``mock`` mode for local development without keys
- ``devnet`` mode for real Solana transactions
- Anchor-compatible account definitions for funding rounds and contributions

Modes
-----

``THRESHOLD_CHAIN_MODE=mock``
   Client scripts do not submit transactions and instead emit realistic structured responses.

``THRESHOLD_CHAIN_MODE=devnet``
   Client scripts connect to the configured RPC URL and validate the presence of a program id and keypair path.

Files
-----

- ``blockchain/Anchor.toml``
- ``blockchain/Cargo.toml``
- ``blockchain/programs/threshold_fund/Cargo.toml``
- ``blockchain/programs/threshold_fund/src/lib.rs``
- ``blockchain/client/deploy.js``
- ``blockchain/client/interact.js``

Suggested workflow
------------------

.. code-block:: bash

   cd blockchain
   npm install
   node client/deploy.js validate-env
   node client/interact.js health

The scaffold intentionally avoids making chain credentials mandatory for the rest of the application stack.
