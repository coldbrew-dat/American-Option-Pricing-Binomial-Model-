# OptiChain

OptiChain is an American option pricing and decision-support application. It uses the Cox-Ross-Rubinstein binomial model to estimate the theoretical value of call and put options, compares that value with the market premium, and gives a simple valuation result.

The project combines a Python pricing backend with a Streamlit frontend. Selected valuation records can also be connected to a local Ganache blockchain through a Solidity smart contract and `web3.py`.

## Project purpose

Option pricing depends on several values, including the stock price, strike price, time to expiry, volatility, risk-free rate, and market premium. OptiChain brings these inputs into one application and makes the pricing process easier to follow through a binomial tree and a clear result screen.

The current project is designed for up to 10 users. The pricing model is kept separate from the interface so that the backend can be reused for separate user sessions.

## Main features

- American call and put option pricing
- CRR binomial option pricing model
- Early-exercise check at every tree node
- Market premium comparison
- Over-valued, under-valued, and fairly valued result
- Binomial stock-price tree visualization
- Volatility sensitivity view
- Streamlit frontend
- User registration and login support
- Local Ganache and smart-contract record keeping
- Calculation history for the connected wallet
- Fingerprint and transaction details for recorded calculations

## Application workflow

1. The user signs up or logs in through the OptiChain frontend.
2. The user enters the option type and pricing inputs.
3. The Python backend validates the values.
4. The CRR binomial model calculates the theoretical American option value.
5. The application compares the theoretical value with the market premium.
6. The result is shown as over-valued, under-valued, or fairly valued.
7. The stock-price tree and volatility sensitivity can be viewed.
8. The valuation can be recorded through the local blockchain setup when Ganache and the smart contract are connected.

## Technologies used

- Python
- Streamlit
- NumPy-compatible Python calculations through the `math` module
- Plotly
- Matplotlib for the standalone tree visualization
- `web3.py`
- Solidity
- Remix IDE
- Ganache
- JSON user record storage for the current local setup

## Project structure

```text
OptiChain/
├── app.py                         # Streamlit frontend and blockchain integration
├── backend.py                     # American option pricing calculations
├── users.json                     # Local user-to-wallet record file
├── assets/                        # Fonts, background, ABI, and other frontend assets
├── contracts/                     # Solidity contract files, if included
├── media/
│   └── optichain-demo.mp4         # Add the project demonstration video here
├── README.md
└── OptiChain_Report.pdf           # Project report, if included in the repository
```

## Installation

Create and activate a virtual environment if required:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\\Scripts\\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the required Python packages:

```bash
pip install streamlit pandas plotly web3 eth-abi matplotlib
```

## Running the application

Start Ganache if the blockchain functions are being used. The current application expects Ganache at:

```text
http://127.0.0.1:7545
```

Make sure the deployed contract address in `app.py` matches the contract deployed on the active Ganache network. Then run the Streamlit application:

```bash
streamlit run app.py
```

Open the local Streamlit address shown in the terminal, usually:

```text
http://localhost:8501
```

## Backend calculation

The main backend function is:

```python
calculate_american_option(...)
```

It calculates:

- The length of each time interval
- Up and down movement factors
- Risk-neutral probabilities
- Expiry stock prices
- Call or put payoffs
- Continuation values
- Immediate exercise values
- The final theoretical option value

For an American option, the model selects the greater value at each node:

```python
node_value = max(continuation_value, exercise_value)
```

This allows the model to account for early exercise.

## Decision labels

The application compares the theoretical option value with the market premium:

- `OVER-VALUED`: market premium is above the model value
- `UNDER-VALUED`: market premium is below the model value
- `FAIRLY VALUED`: the difference is within the selected tolerance

These labels are educational decision-support results and are not investment recommendations.

## Demo video

Add the demonstration video to the repository using this path:

```text
media/optichain-demo.mp4
```

After adding the file, use this link in the README:

[Watch the OptiChain demonstration video](optichain-demo.mp4)

If the video is hosted on YouTube, Google Drive, or another platform, replace the link above with the public video URL.

## Report

The complete project report is available here:

[Open the OptiChain project report](OptiChain_Report.pdf)

## Current limitations

- The application depends on manually entered market inputs unless a market-data source is connected.
- Ganache must be running for the blockchain features.
- The current prototype is intended for a small user group of up to 10 users.
- The current binomial interval control is limited to a small demonstration range.
- The valuation result is an estimate based on model assumptions.
- The application does not execute real trades.

## Future improvements

- Add a production database for user and valuation history.
- Add live market-data integration.
- Add stronger authentication and account management.
- Add deployment support for multiple simultaneous users.
- Add more detailed early-exercise visualizations.
- Add automated tests for the pricing model and frontend workflow.
- Add export of valuation results to PDF or CSV.

## Team

- Sarah Ranta — 24K-5639
- Haadiya Farhan — 24K-5560
- Rumaisa Ali — 24K-5518
