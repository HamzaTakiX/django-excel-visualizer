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

1. Clone the repository:
   ```bash
   git clone https://github.com/HamzaTakiX/django-excel-visualizer.git
   cd django-excel-visualizer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Start the development server:
   ```bash
   python manage.py runserver
   ```

5. Visit http://localhost:8000 in your browser

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

## 💡 Usage

1. **Upload Files**
   - Click "Browse Files" or drag & drop Excel files
   - Supports multiple file upload
   - Automatic format detection

2. **Manage Files**
   - View all uploaded files in a grid layout
   - Sort by name, date, or size
   - Select multiple files for bulk operations
   - Delete individual or multiple files

3. **Visualize Data**
   - Click on a file to view its contents
   - Generate charts and statistics
   - Export in different formats

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Django community for the excellent framework
- Pandas team for data handling capabilities
- Font Awesome for the beautiful icons

## 📧 Contact

For any queries or suggestions, please open an issue on GitHub.