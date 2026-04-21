📦 Leonard Inventory Copilot

A conversational inventory forecasting and replenishment assistant designed to help planners, buyers, and operations teams decide what to order, when to order it, and why.

🚀 Overview

Leonard Inventory Copilot transforms historical sales and inventory data into actionable purchasing decisions.

Instead of just forecasting demand, the system:

Identifies stockout risk
Calculates reorder points and safety stock
Recommends order quantities
Ranks product urgency across the business
Explains decisions in plain English
Allows users to ask natural-language questions about inventory

This tool is designed for environments with:

Large SKU catalogs
Supplier lead times
Seasonal demand patterns
Inventory planning complexity
💡 Key Features
📊 Demand Forecasting
Uses time-series modeling to project future demand
Supports configurable forecast windows
Handles multiple products automatically
📦 Inventory Planning Engine
Calculates:
Average daily demand
Safety stock
Reorder point
Demand during lead time
Generates recommended order quantities
⚠️ Stockout Risk Detection
Classifies products as:
HIGH risk
MEDIUM risk
LOW risk
Highlights items most likely to run out before replenishment arrives
🔥 Urgency Ranking
Scores each product based on:
Inventory gap
Lead time
Days of cover
Sorts products by priority for action
🧠 Conversational Copilot

Ask questions like:

“What should we order?”
“Why is this product risky?”
“Give me a summary”
“Show all products”
“How many days of cover do we have?”

The system responds with business-ready explanations, not technical jargon.

📈 All-Product Recommendation Table
Displays every SKU in one view
Includes:
Inventory
Reorder point
Order quantity
Risk level
Urgency score
Exportable to CSV
🏗️ How It Works
1. Data Input

The system accepts a CSV file containing:

date,product,current_inventory,units_sold,lead_time_days,min_order_qty
2. Forecasting

Each product’s historical sales are analyzed to estimate future demand.

3. Inventory Calculations

For each product:

Demand during lead time
Safety stock
Reorder point
Recommended order quantity
4. Decision Engine

The system evaluates:

Inventory vs reorder point
Days of cover
Lead time exposure

Then determines:

Whether to order
How much to order
Risk level
5. Explanation Layer

Outputs are translated into clear, business language for decision-making.

🧾 Example Output

“Pruning Saw Blades are at risk of stockout. Current inventory covers 18 days of demand, while supplier lead time is 45 days. Projected demand exceeds safe inventory levels, so ordering 420 units now is recommended.”

🛠️ Tech Stack
Python
Streamlit (UI)
Pandas (data processing)
Prophet (forecasting)
Matplotlib (visualization)
📁 Project Structure
inventory-forecasting-bot/
│
├── app.py                  # Main Streamlit app
├── forecast_engine.py      # Demand forecasting logic
├── inventory_math.py       # Inventory calculations
├── requirements.txt        # Dependencies
└── data/                   # Sample data (optional)
▶️ How to Run Locally
1. Clone repo
git clone https://github.com/YOUR_USERNAME/inventory-forecasting-bot.git
cd inventory-forecasting-bot
2. Install dependencies
pip install -r requirements.txt
3. Run app
streamlit run app.py
🌐 Deployment

This app can be deployed using:

Streamlit Community Cloud (recommended)
Docker (future)
Internal company server
📊 Data Compatibility

The system is designed to integrate with:

ERP exports
Inventory management systems
Sales transaction data
Supplier lead time data

Column mapping can be customized in the code for real-world datasets.

🔒 Data Considerations
Do not upload sensitive company data to public repositories
Use local uploads or private repos for real data
Consider anonymized or sampled datasets for demos
🚧 Future Enhancements

Planned improvements include:

Supplier risk dashboard
Open purchase order integration
Margin-based prioritization
Category-level forecasting
Scenario simulation (“What if demand increases 20%?”)
Real AI (LLM) conversational layer
Multi-warehouse support
Automated reorder scheduling
🎯 Use Cases
Inventory planners
Buyers / procurement teams
Operations managers
Supply chain analysts
📣 Value Proposition

This system shifts inventory management from:

“What happened?”

to

“What should we do next?”

👤 Author

Maximus Kaye
Marketing & Management — Ohio Northern University
Wrestler | Business Analytics & Supply Chain Interest

💬 Final Note

This is not just a forecasting tool.

It is a decision-support system designed to help businesses:

prevent stockouts
reduce overstock
improve purchasing timing
and operate more efficiently
