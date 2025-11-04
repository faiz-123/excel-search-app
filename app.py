from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variable to store the current dataframe
current_df = None
current_filename = None

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def load_default_file():
    """Load the default Excel file on startup"""
    global current_df, current_filename
    
    default_file_path = 'nadiad_All_part_merged-filterd.xlsx'
    
    # Try to load from root directory first, then uploads folder
    file_paths = [
        default_file_path,
        os.path.join('uploads', default_file_path)
    ]
    
    for filepath in file_paths:
        if os.path.exists(filepath):
            try:
                current_df = pd.read_excel(filepath)
                # Clean the data - fill NaN values and ensure proper data types
                current_df = current_df.fillna('')
                current_df = current_df.astype(str)
                current_filename = default_file_path
                print(f"✅ Successfully loaded default file: {filepath}")
                print(f"📊 Data shape: {current_df.shape[0]} rows, {current_df.shape[1]} columns")
                return True
            except Exception as e:
                print(f"❌ Error loading {filepath}: {e}")
                continue
    
    print(f"⚠️ Default file '{default_file_path}' not found in root or uploads folder")
    return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    global current_df, current_filename
    
    # Get file info if data is already loaded
    file_info = None
    if current_df is not None:
        file_info = {
            'filename': current_filename,
            'rows': len(current_df),
            'columns': len(current_df.columns),
            'column_names': current_df.columns.tolist()
        }
    
    return render_template('index.html', file_info=file_info)

@app.route('/upload', methods=['POST'])
def upload_file():
    global current_df, current_filename
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Read the Excel/CSV file
            if filename.endswith('.csv'):
                current_df = pd.read_csv(filepath)
            else:
                current_df = pd.read_excel(filepath)
            
            # Clean the data - fill NaN values and ensure proper data types
            current_df = current_df.fillna('')
            current_df = current_df.astype(str)
            
            current_filename = filename
            
            # Get basic info about the data
            info = {
                'filename': filename,
                'rows': len(current_df),
                'columns': len(current_df.columns),
                'column_names': current_df.columns.tolist()
            }
            
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'data': info
            })
            
        except Exception as e:
            return jsonify({'error': f'Error reading file: {str(e)}'}), 400
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/search', methods=['POST'])
def search():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No file uploaded'}), 400
    
    search_data = request.get_json()
    query = search_data.get('query', '').strip()
    column = search_data.get('column', 'all')
    
    if not query:
        return jsonify({'error': 'Search query cannot be empty'}), 400
    
    try:
        # Perform search
        if column == 'all':
            # Search across all columns
            mask = current_df.astype(str).apply(
                lambda x: x.str.contains(query, case=False, na=False)
            ).any(axis=1)
        else:
            # Search in specific column
            if column not in current_df.columns:
                return jsonify({'error': f'Column "{column}" not found'}), 400
            mask = current_df[column].astype(str).str.contains(query, case=False, na=False)
        
        # Filter the dataframe
        filtered_df = current_df[mask]
        
        # Clean the filtered data and convert to JSON-serializable format
        filtered_df = filtered_df.fillna('')
        
        # Convert to list of dictionaries for JSON response
        results = filtered_df.to_dict('records')
        
        return jsonify({
            'success': True,
            'results': results,
            'total_results': len(results),
            'query': query,
            'column': column
        })
        
    except Exception as e:
        return jsonify({'error': f'Search error: {str(e)}'}), 400

@app.route('/get_data')
def get_data():
    global current_df, current_filename
    
    if current_df is None:
        return jsonify({'error': 'No file uploaded'}), 400
    
    # Get pagination parameters
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    # Calculate pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Get page data
    page_data_df = current_df.iloc[start_idx:end_idx]
    page_data_df = page_data_df.fillna('')
    page_data = page_data_df.to_dict('records')
    
    return jsonify({
        'data': page_data,
        'total_rows': len(current_df),
        'page': page,
        'per_page': per_page,
        'total_pages': (len(current_df) + per_page - 1) // per_page,
        'columns': current_df.columns.tolist(),
        'filename': current_filename
    })

@app.route('/export', methods=['POST'])
def export_results():
    global current_df
    
    if current_df is None:
        return jsonify({'error': 'No file uploaded'}), 400
    
    export_data = request.get_json()
    results = export_data.get('results', [])
    
    if not results:
        return jsonify({'error': 'No results to export'}), 400
    
    try:
        # Create DataFrame from results
        export_df = pd.DataFrame(results)
        
        # Export to Excel
        export_filename = f"search_results_{current_filename}"
        export_path = os.path.join(app.config['UPLOAD_FOLDER'], export_filename)
        
        if export_filename.endswith('.csv'):
            export_df.to_csv(export_path, index=False)
        else:
            export_df.to_excel(export_path, index=False)
        
        return send_file(export_path, as_attachment=True, download_name=export_filename)
        
    except Exception as e:
        return jsonify({'error': f'Export error: {str(e)}'}), 400

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Load default Excel file on startup
    load_default_file()
    
    # Get port from environment variable for deployment
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
