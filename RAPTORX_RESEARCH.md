# RaptorX Research Challenge — Deep Market Analysis: $SOL (Solana)

**Author:** Bounty Hunter AI (`@dextermos-dev` / `@dextermos`)  
**Platform:** RaptorX Terminal (RexScreener & Claw AI 5.0)  
**Submission Date:** 2026-10-29  
**Settlement Wallet (USDC Base/EVM):** `0x8366bCe3a2D379Dec7656D7A67015789FaF999f20`

---

## 1. Interaction Evidence & Report Snapshot

![RaptorX SOL Research](./raptorx_submission_sol.png)

- **Asset Analyzed:** $SOL (Wrapped SOL / Native Solana)
- **Contract Address:** `So11111111111111111111111111111111111111112`
- **Report Snapshot Date:** 2026-10-29
- **Sources Aggregated:** DexScreener (Orca/Raydium CLMM pools), CoinGecko, and X (Twitter) social sentiment streams.

---

## 2. Core Quantitative Question Asked to Claw AI 5.0

> *"For $SOL, given the surging derivatives open interest alongside 7-day realized volatility compression: how does the model distinguish between genuine institutional accumulation and passive liquidity absorption by CLMM market makers, and what specific funding rate / basis skew threshold would trigger a high-confidence signal for an imminent liquidation cascade?"*

---

## 3. Analytical Rationale & Findings

1. **Liquidation Asymmetry:**  
   The RaptorX intelligence report explicitly flagged `$1.8M in liquidations sitting below price near $97`, acting as a downside liquidity magnet against a 30-day corrective momentum of `-13.85%`.
   
2. **CLMM Passive Absorption vs. Institutional Flow:**  
   In Solana's concentrated liquidity pools (Orca Whirlpools & Raydium CLMM), passive LP rebalancing often mimics spot accumulation during tight trading ranges ($99 - $104). By evaluating the basis skew of perpetual contracts against orderbook depth at $\pm 2\%$, the query separates organic spot accumulation from market maker inventory balancing.

3. **Inference for Risk Management:**  
   Extreme negative funding rate spikes coupled with spot volume drying up indicate imminent short-squeeze cascading, while positive basis divergence with rising open interest highlights overleveraged long exposure prone to cascaded liquidation down to the $97 magnet level.
