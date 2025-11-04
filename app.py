from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
import json
import logging
import sys
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Add error handler
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return jsonify({'error': 'Internal server error occurred', 'details': str(error)}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return jsonify({'error': f'Application error: {str(e)}', 'type': type(e).__name__}), 500

# Global variable to store the current dataframe
current_df = None
current_filename = None

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def load_default_file():
    """Load the default Excel file on startup"""
    global current_df, current_filename
    
    # Try different files in order of preference
    file_options = [
        'nadiad_All_part_merged-filterd.xlsx',  # Full file
        'nadiad_sample.xlsx',  # Sample file
        os.path.join('uploads', 'nadiad_All_part_merged-filterd.xlsx'),
        os.path.join('uploads', 'nadiad_sample.xlsx')
    ]
    
    for filepath in file_options:
        if os.path.exists(filepath):
            try:
                print(f"🔄 Loading Excel file: {filepath}")
                file_size_mb = os.path.getsize(filepath) / 1024 / 1024
                print(f"📁 File size: {file_size_mb:.2f} MB")
                
                # Load with memory optimization
                current_df = pd.read_excel(filepath, engine='openpyxl')
                
                # Clean the data - fill NaN values and ensure proper data types
                current_df = current_df.fillna('')
                
                # Convert to string but handle memory efficiently
                for col in current_df.columns:
                    current_df[col] = current_df[col].astype(str)
                
                current_filename = os.path.basename(filepath)
                print(f"✅ Successfully loaded file: {filepath}")
                print(f"📊 Data shape: {current_df.shape[0]} rows, {current_df.shape[1]} columns")
                
                memory_usage_mb = current_df.memory_usage(deep=True).sum() / 1024 / 1024
                print(f"🧠 Memory usage: {memory_usage_mb:.2f} MB")
                
                return True
                
            except MemoryError as e:
                print(f"💾 Memory error loading {filepath}: {e}")
                print("⚠️ File too large for available memory, trying next option...")
                continue
            except Exception as e:
                print(f"❌ Error loading {filepath}: {e}")
                continue
    
    print(f"⚠️ No Excel files could be loaded")
    print(f"📁 Current directory files: {[f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls', '.csv'))]}")
    return False

# Load data immediately when module is imported (for gunicorn)
try:
    logger.info("🚀 Starting application...")
    logger.info(f"📁 Current working directory: {os.getcwd()}")
    logger.info(f"📂 Files in current directory: {os.listdir('.')}")
    if current_df is None:  # Only load if not already loaded
        load_default_file()
except Exception as e:
    logger.error(f"❌ Error during startup: {e}")
    # Don't fail completely, allow app to start without data

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/test')
def test():
    """Simple test endpoint"""
    return jsonify({
        'message': 'App is working!',
        'cwd': os.getcwd(),
        'files': os.listdir('.'),
        'templates_dir_exists': os.path.exists('templates'),
        'index_html_exists': os.path.exists('templates/index.html')
    })

@app.route('/health')
def health_check():
    """Health check endpoint for deployment debugging"""
    global current_df, current_filename
    
    status = {
        'status': 'healthy',
        'current_directory': os.getcwd(),
        'files_in_directory': os.listdir('.'),
        'templates_exist': os.path.exists('templates'),
        'index_html_exists': os.path.exists('templates/index.html'),
        'template_folder': app.template_folder,
        'static_folder': app.static_folder,
        'data_loaded': current_df is not None,
        'filename': current_filename,
        'python_version': sys.version,
        'pandas_version': pd.__version__
    }
    
    # Check templates directory
    if os.path.exists('templates'):
        status['template_files'] = os.listdir('templates')
    
    if current_df is not None:
        status['data_shape'] = current_df.shape
        status['columns'] = current_df.columns.tolist()
    
    return jsonify(status)

@app.route('/')
def index():
    global current_df, current_filename
    
    try:
        logger.info("🏠 Accessing home page...")
        logger.info(f"📁 Current directory: {os.getcwd()}")
        logger.info(f"📂 Template folder: {app.template_folder}")
        logger.info(f"📄 Index.html exists: {os.path.exists('templates/index.html')}")
        
        # Get file info if data is already loaded
        file_info = None
        if current_df is not None:
            file_info = {
                'filename': current_filename,
                'rows': len(current_df),
                'columns': len(current_df.columns),
                'column_names': current_df.columns.tolist()
            }
            logger.info(f"📊 Data info: {file_info['filename']} with {file_info['rows']} rows")
        else:
            # Try to load the file if not already loaded
            logger.info("🔄 Data not loaded, attempting to load...")
            load_default_file()
            if current_df is not None:
                file_info = {
                    'filename': current_filename,
                    'rows': len(current_df),
                    'columns': len(current_df.columns),
                    'column_names': current_df.columns.tolist()
                }
        
        logger.info("🎯 Rendering template...")
        return render_template('index.html', file_info=file_info)
    
    except Exception as e:
        logger.error(f"❌ Error in index route: {e}")
        logger.error(f"📍 Traceback: {traceback.format_exc()}")
        
        # Return a simple HTML response if template fails
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Excel Search - Error</title></head>
        <body>
            <h1>Excel Search Application</h1>
            <p>Template loading error: {str(e)}</p>
            <p>Current directory: {os.getcwd()}</p>
            <p>Template folder: {app.template_folder}</p>
            <p>Files: {os.listdir('.')}</p>
            <a href="/health">Check Health Status</a>
        </body>
        </html>
        """
        return html_content, 500

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
        # Try to load the file if not loaded
        load_default_file()
        if current_df is None:
            return jsonify({'error': 'No file loaded and unable to load default file'}), 400
    
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 100)  # Limit to 100 per page
        
        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get page data
        page_data_df = current_df.iloc[start_idx:end_idx].copy()
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
    
    except Exception as e:
        print(f"❌ Error in get_data: {e}")
        return jsonify({'error': f'Error retrieving data: {str(e)}'}), 500

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
