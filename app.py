from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os

# Initialize the Flask application
app = Flask(__name__)

# Configure the upload folder for file uploads
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the upload folder exists; create it if it doesn't
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    """
    Handles the root URL '/' of the web application.

    @param: None
    @return: Rendered HTML template for the index page.
    """
    # Render the 'index.html' file located in the 'templates' folder.
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handles file uploads, processes the file (CSV/JSON), and cleans the data.

    @param: None (receives uploaded file via POST request)
    @return: Renders the result.html page with cleaned data or an error message.
    """
    # Check if the POST request contains a file part
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']

    # Check if the file has a valid name
    if file.filename == '':
        return "No selected file"

    # Process the file if it exists
    if file:
        # Define the file path for saving the uploaded file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

        # Save the uploaded file to the designated path
        file.save(file_path)

        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)  # Load CSV file
        elif file.filename.endswith('.json'):
            df = pd.read_json(file_path)  # Load JSON file
        else:
            return "Unsupported file format"

        # Clean column names: lowercased and replace spaces with underscores
        df.columns = df.columns.str.lower().str.replace(' ', '_')

        # Clean the 'country' column if it exists
        if 'country' in df.columns:
            df['country'] = df['country'].str.strip().str.title()

        # Drop rows with missing values
        df = df.dropna()

        # Remove duplicate rows
        df = df.drop_duplicates()

        # Check if required columns exist for aggregation
        if {'country', 'date', 'cases', 'deaths', 'recovered'}.issubset(df.columns):
            # Aggregate data by country and date, summing up the cases, deaths, and recoveries
            df = df.groupby(['country', 'date']).agg({
                'cases': 'sum',
                'deaths': 'sum',
                'recovered': 'sum'
            }).reset_index()

        # Save the cleaned data to a new CSV file
        cleaned_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'cleaned_data.csv')
        df.to_csv(cleaned_file_path, index=False)

        # Render the result page with the cleaned data in an HTML table
        return render_template(
            'result.html',
            tables=[df.to_html(classes='table table-striped')],
            filename='cleaned_data.csv'
        )


@app.route('/download/<filename>')
def download_file(filename):
    """
    Handles file download requests by redirecting to the file's path.

    @param: filename (str) - The name of the file to be downloaded.
    @return: A redirect response pointing to the file's location.
    """
    # Construct the full file path based on the upload folder and the filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Redirect the user to the file's URL for downloading
    return redirect(f"/{file_path}")


if __name__ == '__main__':
    app.run(debug=True)
