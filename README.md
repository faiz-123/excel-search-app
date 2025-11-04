# Excel Data Search Web Application

A Flask web application that allows you to upload Excel files and search through large datasets with a user-friendly interface.

## Features

- **File Upload**: Support for Excel (.xlsx, .xls) and CSV files
- **Smart Search**: Search across all columns or specific columns
- **Responsive Design**: Works on desktop and mobile devices
- **Pagination**: Handle large datasets efficiently
- **Export Results**: Download search results as Excel files
- **Drag & Drop**: Easy file upload with drag and drop support

## Installation

1. Make sure you have Python 3.9+ installed
2. The virtual environment and dependencies are already set up in this workspace

## Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Open your browser** and go to `http://localhost:5000`

3. **Upload your Excel file**:
   - Click the upload area or drag and drop your file
   - Supported formats: .xlsx, .xls, .csv
   - Maximum file size: 16MB

4. **Search your data**:
   - Enter search terms in the search box
   - Choose to search all columns or a specific column
   - View results in an organized table

5. **Export results**:
   - Click "Export Results" to download filtered data
   - Results are saved as Excel files

## File Structure

```
sir/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Web interface
├── static/               # CSS and JS files (embedded in HTML)
├── uploads/              # Uploaded files storage
└── .venv/               # Virtual environment
```

## Technical Details

- **Backend**: Flask (Python web framework)
- **Data Processing**: Pandas for Excel/CSV handling
- **File Handling**: Secure file upload and processing
- **Frontend**: Responsive HTML/CSS/JavaScript
- **Search**: Case-insensitive text search across columns

## Example Data Format

The application works with any Excel data. For example, if you have data like:

| વિભાગ | અનુ. નંબર | ઘર | અંતિમ નામ | પ્રથમ નામ | સંબંધ |
|-------|-----------|-----|----------|----------|-------|
| 33    | 1         | 321 | ચૌહાણ    | મંગળભાઈ  | પિ.   |
| 33    | 2         | 321 | ચૌહાણ    | મોતીબેન   | ૫.    |

You can search for:
- Names: "મંગળભાઈ", "ચૌહાણ"
- Numbers: "33", "321"
- Any text that appears in your data

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Troubleshooting

1. **File won't upload**: Check file format (.xlsx, .xls, .csv) and size (<16MB)
2. **Search not working**: Make sure file is uploaded successfully first
3. **Application won't start**: Check Python environment is activated

## Security Features

- Secure file upload with filename sanitization
- File type validation
- Maximum file size limits
- No data stored permanently (files in uploads/ folder)
