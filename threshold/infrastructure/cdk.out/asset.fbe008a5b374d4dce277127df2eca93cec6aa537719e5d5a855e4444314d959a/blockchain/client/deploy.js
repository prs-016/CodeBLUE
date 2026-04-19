require("dotenv").config({ path: require("path").resolve(__dirname, "../../.env") });

const fs = require("fs");
const path = require("path");
const { Keypair, Connection, PublicKey } = require("@solana/web3.js");
const REPO_ROOT = path.resolve(__dirname, "../..");

function readJsonKeypair(filePath) {
  const resolved = path.resolve(REPO_ROOT, filePath);
  const secret = JSON.parse(fs.readFileSync(resolved, "utf8"));
  return Keypair.fromSecretKey(Uint8Array.from(secret));
}

function getConfig() {
  return {
    mode: process.env.THRESHOLD_CHAIN_MODE || "mock",
    rpcUrl: process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com",
    programId: process.env.SOLANA_PROGRAM_ID || "",
    keypairPath: process.env.SOLANA_KEYPAIR_PATH || "",
  };
}

async function validateEnv() {
  const config = getConfig();
  const result = {
    mode: config.mode,
    rpcUrl: config.rpcUrl,
    programConfigured: Boolean(config.programId),
    keypairConfigured: Boolean(config.keypairPath),
  };

  if (config.mode === "mock") {
    return {
      ok: true,
      message: "Mock mode enabled. No on-chain credentials required.",
      ...result,
    };
  }

  if (!config.programId || !config.keypairPath) {
    return {
      ok: false,
      message: "Devnet mode requires SOLANA_PROGRAM_ID and SOLANA_KEYPAIR_PATH.",
      ...result,
    };
  }

  try {
    const payer = readJsonKeypair(config.keypairPath);
    const programId = new PublicKey(config.programId);
    const connection = new Connection(config.rpcUrl, "confirmed");
    const balance = await connection.getBalance(payer.publicKey);
    return {
      ok: true,
      message: "Devnet configuration looks usable.",
      payer: payer.publicKey.toBase58(),
      programId: programId.toBase58(),
      lamports: balance,
      ...result,
    };
  } catch (error) {
    return {
      ok: false,
      message: error.message,
      ...result,
    };
  }
}

async function main() {
  const command = process.argv[2] || "validate-env";

  if (command === "validate-env") {
    const output = await validateEnv();
    console.log(JSON.stringify(output, null, 2));
    process.exit(output.ok ? 0 : 1);
  }

  console.error(`Unknown command: ${command}`);
  process.exit(1);
}

main();
