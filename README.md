# Savings Goal Tracker

## Overview
The Savings Goal Tracker is a web application built using Streamlit that helps users set and track their savings goals. Users can input their savings goal and current savings, visualize their progress through a progress bar, and receive feedback on their savings performance with a happiness meter.

## Features
- Set a savings goal (e.g., $6000).
- Input current savings amount.
- Visualize progress towards the savings goal with a progress bar.
- Display how far the user is from their goal.
- Track monthly savings performance and adjust the happiness meter accordingly.

## Project Structure
```
savings-goal-tracker
├── app.py                # Main entry point of the Streamlit application
├── requirements.txt      # Lists the dependencies required for the project
├── static
│   └── style.css         # CSS styles for the application
├── utils
│   └── savings_tracker.py # Utility functions for managing savings data
└── README.md             # Documentation for the project
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd savings-goal-tracker
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit application:
   ```
   streamlit run app.py
   ```

## Usage Guidelines
- Open the application in your web browser.
- Enter your savings goal and current savings.
- The application will display a progress bar indicating your progress towards your goal.
- If your savings decrease in the following month, the happiness meter will reflect your performance.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License
This project is licensed under the MIT License.