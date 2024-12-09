# Excel Visualization Web Application

A powerful Django-based web application for uploading, managing, and visualizing Excel files. This application provides an intuitive interface for data analysis and visualization, making it easy to work with Excel data in a web browser.

## 🚀 Features

- **File Management**
  - Excel file upload with drag & drop support
  - Multiple file upload with progress tracking
  - File size validation (max 10MB per file)
  - Support for XLSX, XLS, and CSV formats
  - File listing with metadata (size, rows, columns)
  - Batch operations (select multiple, delete)
  - Individual file deletion
  - Download files in multiple formats (XLSX, CSV)
  - Real-time last modification tracking
  - File information cards with animations
  - Loading states with modern animations

- **Data Visualization & Analysis**
  - Interactive data tables with search functionality
  - Modern pagination controls (6 items per page)
  - Multiple chart types:
    - Line charts
    - Bar charts
    - Pie charts
  - Dynamic chart generation
  - Responsive visualizations
  - Comprehensive statistical calculations:
    - Mean, Median, Mode
    - Sum, Count
    - Standard Deviation
    - Variance
  - Real-time statistics updates
  - Copy-to-clipboard functionality

- **Modern User Interface**
  - Sleek, responsive design
  - Gradient-based color scheme
  - Animated components and transitions
  - Modern card-based layout
  - Interactive buttons and controls
  - Floating animations and shadows
  - Toast notifications with animations
  - Mobile-friendly interface
  - Real-time edit tracking
  - Loading overlays with blur effects

- **Enhanced Data Table Features**
  - Modern gradient headers
  - Row hover effects
  - Advanced search and filtering
  - Smooth animations
  - Inline editing capabilities
  - Format selection for downloads
  - Real-time data updates
  - Bulk selection and operations

## 🎨 Design Features

- **Color Scheme**
  - Primary color: #007bff
  - Secondary colors: #0056b3, #2c3e50
  - Light backgrounds with gradients
  - Consistent color palette
  - Modern blur effects

- **Typography**
  - Modern font stack
  - Responsive text sizing
  - Enhanced readability
  - Consistent spacing
  - Font Awesome icons integration

- **Animations**
  - Smooth transitions
  - Hover effects
  - Loading spinners
  - Toast notifications
  - Card hover effects
  - Bounce animations
  - Fade effects

## 🛠️ Technologies Used

- **Backend**
  - Python 3.x
  - Django 4.2.16
  - Pandas 2.2.3
  - NumPy 2.0.0
  - OpenPyXL 3.1.2
  - XlRD 2.0.1
  - Python Magic 0.4.27
  - Pillow 10.2.0

- **Frontend**
  - HTML5
  - CSS3 (Modern features)
  - Vanilla JavaScript
  - Font Awesome icons
  - Custom animations
  - Modern CSS Grid/Flexbox
  - Responsive design
  - Dynamic loading states

## 📋 Prerequisites

Before running the project, make sure you have:

- Python 3.x installed
- pip (Python package manager)
- Git (for cloning)
- Web browser (Chrome, Firefox, or Edge recommended)

## 🚀 Installation

1. **Get the Project**
   ```bash
   # Clone the repository (if using Git)
   git clone [repository-url]
   # Or download and extract the ZIP file
   
   # Navigate to project directory
   cd my_dango_projecta
   ```

2. **Set Up Python Environment**
   ```bash
   # Create virtual environment
   python -m venv env
   
   # Activate virtual environment
   # On Windows:
   env\Scripts\activate
   # On macOS/Linux:
   source env/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   # Install required packages
   pip install -r requirements.txt
   ```

4. **Database Setup**
   ```bash
   # Apply database migrations
   python manage.py makemigrations
   python manage.py migrate
   ```

## 🚀 Running the Project

1. **Start Development Server**
   ```bash
   source env/Scripts/activate
   python manage.py runserver
   ```
   The application will be available at `http://127.0.0.1:8000/`

2. **Access the Application**
   - Open your web browser
   - Go to `http://127.0.0.1:8000/`
   - You should see the Excel Visualization homepage

3. **Using the Application**
   - Click "Upload" to add Excel files
   - View uploaded files in the file list
   - Click on a file to view its contents
   - Use visualization options to create charts
   - Download processed data as CSV

4. **Stopping the Server**
   - Press `Ctrl+C` in the terminal to stop the server
   - Deactivate the virtual environment:
     ```bash
     deactivate
     ```

## 🔍 Troubleshooting

Common issues and solutions:

1. **Port Already in Use**
   ```bash
   # Use a different port
   python manage.py runserver 8001
   ```

2. **Package Installation Issues**
   ```bash
   # Upgrade pip
   python -m pip install --upgrade pip
   # Then reinstall requirements
   pip install -r requirements.txt
   ```

3. **Database Issues**
   ```bash
   # Reset database
   python manage.py flush
   python manage.py migrate
   ```

## 📁 Project Structure

```
django-excel-visualizer/
├── Excel_App/            # Main application
│   ├── static/          # Static files (CSS, JS)
│   ├── templates/       # HTML templates
│   ├── views.py        # View functions
│   ├── urls.py         # URL configurations
│   └── models.py       # Data models
├── Excel_Visualization/ # Project settings
├── media/              # Uploaded files
└── requirements.txt    # Dependencies
```

## 🔒 Security Features

- File type validation
- Secure file handling
- Session-based operations
- Error handling and validation

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- [hamza taki]

## 📧 Contact

For any queries or support, please contact [hazoakaka@gmail.com]

## 🔄 Recent Updates

### December 2024 Updates
- **CSV File Handling**
  - Enhanced support for CSV files with multiple encoding options
  - Improved error handling for file reading
  - Automatic detection of file types

- **Error Handling Improvements**
  - More descriptive error messages for file processing
  - Robust handling of various file formats

- **Backend Enhancements**
  - Updated file reading logic to handle different file types
  - Improved file processing efficiency

- **UI Improvements**
  - Consistent display of file information and error messages

### December 2024 Updates
- **Enhanced Time Tracking**
  - Added separate tracking for file upload time and last modification time
  - Automatic updates of last modified time when saving changes
  - Improved timestamp display format (YYYY-MM-DD HH:MM:SS)
  - Visual distinction between upload time and last edit time

- **UI Improvements**
  - Added "Last Edit" badge to modification time display
  - Enhanced info cards with consistent styling
  - Improved time format display across all views
  - Real-time updates of modification time on save

- **Backend Enhancements**
  - Improved timestamp handling in Django models
  - Added auto-updating last_modified field
  - Enhanced time formatting in API responses
  - Better error handling for file operations