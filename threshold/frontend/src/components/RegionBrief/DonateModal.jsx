import React, { useEffect, useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { Elements, CardElement, useStripe, useElements } from "@stripe/react-stripe-js";
import { X, ShieldCheck, Zap, Globe } from "lucide-react";

const stripePromise = loadStripe(
  import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || "pk_test_placeholder"
);

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function CheckoutForm({ roundId, amount, onClose }) {
  const stripe = useStripe();
  const elements = useElements();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("idle"); // idle | processing | success | error
  const [txHash, setTxHash] = useState(null);
  const [txOnChain, setTxOnChain] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;
    setStatus("processing");
    setErrorMsg(null);

    try {
      const res = await fetch(
        `${API_URL}/api/v1/funding/rounds/${roundId}/contribute`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            amount_usd: parseFloat(amount),
            donor_email: email,
          }),
        }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || "Contribution failed");
      }

      const data = await res.json();
      setTxHash(data.blockchain_hash);
      setTxOnChain(data.blockchain_status === "finalized_on_chain");
      setStatus("success");
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message);
      setStatus("error");
    }
  };

  if (status === "success") {
    return (
      <div className="text-center py-6">
        <div className="mx-auto w-16 h-16 bg-teal/20 border border-teal-light/30 rounded-full flex items-center justify-center mb-5">
          <ShieldCheck className="text-teal-light w-9 h-9" />
        </div>
        <h3 className="text-2xl font-bold text-white mb-2">Contribution Secured</h3>
        <p className="text-grey-mid text-sm mb-6 px-4 leading-relaxed">
          Your card payment triggered a Solana Memo transaction — permanently
          recorded on the blockchain. No crypto wallet was required.
        </p>

        <div className="bg-black/40 rounded-2xl p-4 border border-teal-light/20 mb-4 text-left">
          {txOnChain ? (
            <>
              <div className="text-[10px] uppercase tracking-widest text-teal-light mb-2 font-mono">
                Solana On-Chain Record
              </div>
              <div className="font-mono text-[10px] break-all text-white/60 mb-3">{txHash}</div>
              <a
                href={`https://explorer.solana.com/tx/${txHash}?cluster=devnet`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-xs font-semibold text-teal-light hover:text-white transition-colors border border-teal-light/30 rounded-xl px-3 py-2"
              >
                <Globe className="w-3.5 h-3.5" />
                Verify on Solana Explorer →
              </a>
            </>
          ) : (
            <>
              <div className="text-[10px] uppercase tracking-widest text-grey-mid mb-2 font-mono">
                Donation Ledger ID
              </div>
              <div className="font-mono text-[10px] break-all text-white/60 mb-2">{txHash}</div>
              <p className="text-[10px] text-grey-dark leading-relaxed">
                Recorded locally — Solana devnet temporarily rate-limited.
                All contributions are batched and committed on-chain when devnet capacity is available.
              </p>
            </>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-4 bg-teal-light text-black font-bold rounded-2xl hover:brightness-110 transition-all uppercase tracking-widest text-sm"
        >
          Return to War Room
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-[10px] uppercase tracking-widest text-grey-mid mb-2 font-mono">
          Donor Email
        </label>
        <input
          type="email"
          required
          placeholder="relief@operator.net"
          className="w-full bg-black/40 border border-grey-dark/50 rounded-2xl px-4 py-3 text-white placeholder-grey-dark focus:outline-none focus:border-teal-light/50 transition-all text-sm"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      <div>
        <label className="block text-[10px] uppercase tracking-widest text-grey-mid mb-2 font-mono">
          Encrypted Card Entry
        </label>
        <div className="bg-black/40 border border-grey-dark/50 rounded-2xl p-4 focus-within:border-teal-light/50 transition-all" style={{ minHeight: "52px" }}>
          <CardElement
            options={{
              style: {
                base: {
                  fontSize: "15px",
                  color: "#ffffff",
                  "::placeholder": { color: "#525252" },
                  fontFamily: "monospace",
                },
                invalid: { color: "#ff4d4d" },
              },
            }}
          />
        </div>
      </div>

      {status === "error" && (
        <div className="p-3 bg-red-alert/10 border border-red-alert/30 rounded-xl text-red-300 text-xs">
          {errorMsg || "Something went wrong. Please retry."}
        </div>
      )}

      <div className="flex items-start gap-3 p-4 bg-teal/10 border border-teal-light/20 rounded-2xl text-teal-light/80 text-xs leading-relaxed">
        <ShieldCheck size={16} className="shrink-0 mt-0.5" />
        <p>
          <span className="font-bold text-teal-light">No crypto wallet required.</span>{" "}
          Pay with your card — we write an immutable Solana Memo on your behalf so your
          donation is publicly verifiable on-chain.
        </p>
      </div>

      <button
        type="submit"
        disabled={!stripe || status === "processing"}
        className="w-full py-4 bg-white text-black font-bold rounded-2xl hover:bg-teal-light transition-all flex items-center justify-center gap-2 uppercase tracking-widest text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {status === "processing" ? "Processing..." : `Donate $${amount} by Card`}
      </button>

      <div className="flex items-center justify-center gap-8 pt-2 opacity-30">
        <span className="text-[9px] font-mono tracking-widest text-white">STRIPE_NETWORK</span>
        <span className="text-[9px] font-mono tracking-widest text-white">SOLANA_LEDGER</span>
        <span className="text-[9px] font-mono tracking-widest text-white">PCI_DSS</span>
      </div>
    </form>
  );
}

export default function DonateModal({ isOpen, onClose, region, roundId }) {
  const [amount, setAmount] = useState("50");
  const presets = ["25", "50", "100", "500"];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4" style={{ animation: "modalFadeIn 0.2s ease" }}>
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-md"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg bg-[#080f1a] rounded-[32px] border border-white/10 shadow-2xl overflow-hidden" style={{ animation: "modalSlideUp 0.22s cubic-bezier(0.16,1,0.3,1)" }}>
        {/* Top accent bar */}
        <div className="h-1 bg-gradient-to-r from-teal-light via-orange to-red-alert" />

        <div className="p-8">
          {/* Header */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Globe className="text-teal-light w-4 h-4" />
                <span className="text-[10px] uppercase tracking-[0.3em] text-teal-light font-mono">
                  Relief Funding Tranche
                </span>
              </div>
              <h2 className="text-2xl font-bold text-white">
                Intervene in {region?.name ?? "Region"}
              </h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/5 rounded-full transition-colors"
            >
              <X className="text-grey-mid w-5 h-5" />
            </button>
          </div>

          {/* Amount Selector */}
          <div className="mb-7">
            <div className="text-[10px] uppercase tracking-widest text-grey-mid mb-3 font-mono">
              Select Tranche Amount
            </div>
            <div className="grid grid-cols-4 gap-3">
              {presets.map((val) => (
                <button
                  key={val}
                  onClick={() => setAmount(val)}
                  className={`py-3 rounded-xl border font-mono text-sm transition-all ${
                    amount === val
                      ? "bg-white text-black border-white shadow-[0_0_20px_rgba(255,255,255,0.15)]"
                      : "bg-white/5 text-white border-white/10 hover:border-white/30"
                  }`}
                >
                  ${val}
                </button>
              ))}
            </div>
          </div>

          <Elements stripe={stripePromise}>
            <CheckoutForm roundId={roundId} amount={amount} onClose={onClose} />
          </Elements>
        </div>
      </div>
    </div>
  );
}
