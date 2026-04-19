import time
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.message import MessageV0
from solders.transaction import VersionedTransaction

def test():
    client = Client("https://api.devnet.solana.com")
    kp = Keypair()
    print("Pubkey:", kp.pubkey())
    
    try:
        print("Requesting Airdrop...")
        resp = client.request_airdrop(kp.pubkey(), int(1e9)) # 1 SOL
        print("Airdrop resp:", resp)
        time.sleep(15) # Wait for confirmation
    except Exception as e:
        print("Airdrop failed:", e)
    
    memo_program = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLXFmXQ_")
    text = "pytest memo"
    
    ix = Instruction(
        program_id=memo_program,
        accounts=[AccountMeta(pubkey=kp.pubkey(), is_signer=True, is_writable=True)],
        data=text.encode('utf-8')
    )
    
    try:
        blockhash = client.get_latest_blockhash().value.blockhash
        msg = MessageV0.try_compile(
            payer=kp.pubkey(),
            instructions=[ix],
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash,
        )
        tx = VersionedTransaction(msg, [kp])
        res = client.send_transaction(tx)
        print("Success! TX Signature:", res.value)
    except Exception as e:
        print("Send failed:", e)

test()
