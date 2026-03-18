# Unilights Query Chatbot 🤖

An intelligent business assistant designed for **Unilights**, a lighting manufacturing company. This application provides a natural language interface to query complex inventory, order, and Bill of Materials (BOM) data stored in Excel spreadsheets.

## 🌟 Features

- **Order Intelligence**: Query order status, customer history, and dispatch plans.
- **BOM Intelligence Engine**: 
    - Full Bill of Materials breakdown with cost analysis.
    - Support for "Product Family" files with complex SKU attribute mappings.
    - Variant comparison and batch production planning.
- **AI Engine**: Uses Anthropic Claude 3.5 Sonnet for accurate tool selection and human-friendly response generation.
- **Modern UI**: Clean and interactive interface built with Streamlit.

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Data Processing**: [Pandas](https://pandas.pydata.org/), [Openpyxl](https://openpyxl.readthedocs i.o/)
- **AI Engine**: [Anthropic Claude](https://anthropic.com/)
- **Environment**: [Python Dotenv](https://pypi.org/project/python-dotenv/)

## 🚀 Getting Started

### Prerequisites

- A Python 3.9 or higher environment.
- An Anthropic API Key.

### Installation

1. **Clone the repository** (if applicable) or navigate to the project directory.
2. **Install dependencies**:
   ```bash
   pip install streamlit pandas anthropic python-dotenv openpyxl
   ```
3. **Configure Environment**:
   Create a `.env` file in the root directory and add your Anthropic API key:
   ```env
   ANTHROPIC_API_KEY=your_api_key_here
   ```

### Running the Application

Start the Streamlit dashboard using the following command:

```bash
streamlit run streamlit_app.py
```

The app will typically be available at `http://localhost:8501`.

## 📁 Project Structure

- `streamlit_app.py`: Main entry point and user interface.
- `agent.py`: Core logic for the Gemini agent and tool definitions.
- `tools.py`: Collection of 12 specialized data query tools.
- `bom_loader.py`: Advanced parser for Bill of Materials Excel files.
- `data_loader.py`: General utility for loading order and inventory sheets.
- `data/`: Directory containing source Excel data files.
- `scripts/`: Utility and testing scripts.

## 📝 Usage & Testing Guide

To test the full capabilities of the Unilights Chatbot, try the following queries across three levels of complexity:

### 🟢 Level 1: Easy (Basic Queries)
*Simple data retrieval for products and customers.*
- "List all products available in the system."
- "Show me all orders from the customer 'J.R. Electro'."
- "What is the order history for 'K.P. Enterprises'?"
- "Is there any model named 'TTLB24W' in the data?"

### 🟡 Level 2: Medium (Departmental & Status Queries)
*Tracking production stages and specific item statuses.*
- "Tell me the delivery status of model 'SRDR12W-COB'."
- "What items are currently ready in the 'Electronic Store'?"
- "Show all orders that are currently 'On Hold'."
- "List all products that are packed and ready for dispatch."
- "What is the manufacturing cost for 'SBDR-24W'?"

### 🔴 Level 3: Advanced (BOM & Intelligence Queries)
*Complex calculations, material planning, and variant comparisons.*
- "Calculate the total materials needed to produce 500 units of 'SRDR12W-COB' and 200 units of 'TTLB24W'."
- "Compare the Bill of Materials for 'SRDR12W-COB' and 'SRDR12W-SMD'. What are the cost differences?"
- "Which products use 'COB LED' as a component?"
- "Find all products that require 'Driver 12W' and show their production status."
- "Show a high-level dashboard summary of all loaded data."
