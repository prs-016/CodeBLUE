require("dotenv").config({ path: require("path").resolve(__dirname, "../../.env") });

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { Connection, Keypair, PublicKey, clusterApiUrl } = require("@solana/web3.js");
const REPO_ROOT = path.resolve(__dirname, "../..");

function resolveRpcUrl() {
  return process.env.SOLANA_RPC_URL || clusterApiUrl("devnet");
}

function getMode() {
  return process.env.THRESHOLD_CHAIN_MODE || "mock";
}

function loadKeypairIfPresent() {
  const keypairPath = process.env.SOLANA_KEYPAIR_PATH;
  if (!keypairPath) {
    return null;
  }

  const resolved = path.resolve(REPO_ROOT, keypairPath);
  if (!fs.existsSync(resolved)) {
    return null;
  }

  const secret = JSON.parse(fs.readFileSync(resolved, "utf8"));
  return Keypair.fromSecretKey(Uint8Array.from(secret));
}

function buildMockTx(prefix) {
  return `${prefix}_${Date.now()}_${crypto.randomBytes(4).toString("hex")}`;
}

class ThresholdFundClient {
  constructor() {
    this.mode = getMode();
    this.rpcUrl = resolveRpcUrl();
    this.programId = process.env.SOLANA_PROGRAM_ID || "";
    this.connection = new Connection(this.rpcUrl, "confirmed");
    this.wallet = loadKeypairIfPresent();
  }

  isConfiguredForDevnet() {
    return this.mode === "devnet" && this.wallet && this.programId;
  }

  async health() {
    if (this.mode === "mock") {
      return {
        ok: true,
        mode: "mock",
        rpcUrl: this.rpcUrl,
        message: "Blockchain client is running in mock mode.",
      };
    }

    if (!this.isConfiguredForDevnet()) {
      return {
        ok: false,
        mode: "devnet",
        rpcUrl: this.rpcUrl,
        message: "Missing SOLANA_PROGRAM_ID or SOLANA_KEYPAIR_PATH for devnet mode.",
      };
    }

    const blockHeight = await this.connection.getBlockHeight("confirmed");
    return {
      ok: true,
      mode: "devnet",
      rpcUrl: this.rpcUrl,
      programId: new PublicKey(this.programId).toBase58(),
      wallet: this.wallet.publicKey.toBase58(),
      blockHeight,
    };
  }

  async initializeRound(regionId, targetAmount, deadline, charityWallets = []) {
    if (!this.isConfiguredForDevnet()) {
      return {
        status: "mock",
        txHash: buildMockTx("init"),
        roundPda: buildMockTx("round"),
        regionId,
        targetAmount,
        deadline,
        charityWallets,
      };
    }

    return {
      status: "pending_integration",
      message: "Anchor RPC wiring is not connected yet; account schema is scaffolded.",
      regionId,
      targetAmount,
      deadline,
      charityWallets,
    };
  }

  async recordContribution(roundId, amount, donorHash) {
    if (!this.isConfiguredForDevnet()) {
      return {
        status: "mock",
        txHash: buildMockTx("contrib"),
        roundId,
        amount,
        donorHash,
      };
    }

    return {
      status: "pending_integration",
      message: "Contribution recording is scaffolded but not yet invoking Anchor RPC.",
      roundId,
      amount,
      donorHash,
    };
  }

  async disburse(roundId, trancheIndex, charityWallet, amount, progressReportHash = "") {
    if (!this.isConfiguredForDevnet()) {
      return {
        status: "mock",
        txHash: buildMockTx("disburse"),
        roundId,
        trancheIndex,
        charityWallet,
        amount,
        progressReportHash,
      };
    }

    return {
      status: "pending_integration",
      message: "Disbursement flow awaits backend + Anchor RPC integration.",
      roundId,
      trancheIndex,
      charityWallet,
      amount,
      progressReportHash,
    };
  }

  async getTransactionHistory(roundId) {
    if (!this.isConfiguredForDevnet()) {
      return [
        {
          signature: buildMockTx("sig"),
          roundId,
          amount: 50,
          time: new Date().toISOString(),
          mode: "mock",
        },
      ];
    }

    return [];
  }
}

async function main() {
  const client = new ThresholdFundClient();
  const command = process.argv[2] || "health";

  switch (command) {
    case "health":
      console.log(JSON.stringify(await client.health(), null, 2));
      return;
    case "init-round":
      console.log(
        JSON.stringify(
          await client.initializeRound(
            process.argv[3] || "great_barrier_reef",
            Number(process.argv[4] || 1000000),
            Number(process.argv[5] || Math.floor(Date.now() / 1000) + 86400 * 30),
            []
          ),
          null,
          2
        )
      );
      return;
    case "record-contribution":
      console.log(
        JSON.stringify(
          await client.recordContribution(
            process.argv[3] || "demo-round",
            Number(process.argv[4] || 50),
            process.argv[5] || crypto.createHash("sha256").update("demo@example.com").digest("hex")
          ),
          null,
          2
        )
      );
      return;
    default:
      console.error(`Unknown command: ${command}`);
      process.exit(1);
  }
}

main();

module.exports = { ThresholdFundClient };
