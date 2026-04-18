const anchor = require('@coral-xyz/anchor');
const { Connection, PublicKey, Keypair } = require('@solana/web3.js');
// Mocking IDL load
// const idl = require('../target/idl/threshold_fund.json');

const PROGRAM_ID = new PublicKey("ThResH1...9zQ2");
const DEVNET_URL = "https://api.devnet.solana.com";

class ThresholdFundClient {
  constructor(walletPath) {
    this.connection = new Connection(DEVNET_URL, 'confirmed');
    // MOCK: Setup provider and program
    // const wallet = new anchor.Wallet(Keypair.fromSecretKey(load(walletPath)));
    // this.provider = new anchor.AnchorProvider(this.connection, wallet, {});
    // this.program = new anchor.Program(idl, PROGRAM_ID, this.provider);
  }

  async initializeRound(regionId, targetAmount, deadline, charityWallets) {
    console.log(`[MOCK ON-CHAIN] Init Round for ${regionId} - Target: ${targetAmount}`);
    return { status: 'success', txHash: 'mock_init_tx_' + Date.now() };
  }

  async recordContribution(roundId, amount, donorHash) {
    console.log(`[MOCK ON-CHAIN] Record Contribution to ${roundId} - Amount: ${amount}`);
    return { status: 'success', txHash: 'mock_contrib_tx_' + Date.now() };
  }

  async disburse(roundId, trancheIndex, charityWallet, amount) {
    console.log(`[MOCK ON-CHAIN] Disburse Tranche ${trancheIndex} to ${charityWallet.toBase58()}`);
    return { status: 'success', txHash: 'mock_disburse_tx_' + Date.now() };
  }

  async getTransactionHistory(roundId) {
    // Return mock historical transactions
    return [
      { signature: "5dJqXp...", amount: 500, time: new Date().toISOString() },
      { signature: "8pLvZm...", amount: 1500, time: new Date().toISOString() }
    ];
  }
}

module.exports = { ThresholdFundClient };
