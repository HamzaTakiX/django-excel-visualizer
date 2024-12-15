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

- **Advanced Data Visualization**
  - Interactive data tables with search functionality
  - Modern pagination controls (6 items per page)
  - Multiple chart types:
    - Line charts with customizable styles
    - Bar charts with dynamic aggregation
    - Pie charts with percentage display
    - Scatter plots with markers
    - Heatmaps with color gradients
    - Box plots for distribution analysis
    - Violin plots for density visualization
  - Dynamic chart generation with real-time updates
  - Responsive visualizations that adapt to screen size
  - Modern UI controls:
    - Color pickers for customization
    - Reset functionality for quick iterations
    - Centered button layout
    - Gradient-based styling

- **Statistical Analysis**
  - Comprehensive statistical calculations:
    - Mean, Median, Mode
    - Sum, Count
    - Standard Deviation
    - Variance
    - Probability calculations
  - Real-time statistics updates
  - Copy-to-clipboard functionality

- **Modern User Interface**
  - Sleek, responsive design
  - Gradient-based color scheme
  - Animated components and transitions
  - Modern card-based layout
  - Interactive buttons with hover effects
  - Floating animations and shadows
  - Toast notifications with animations
  - Mobile-friendly interface
  - Real-time edit tracking
  - Loading overlays with blur effects

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/django-excel-visualizer.git
cd django-excel-visualizer
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

## 📊 Usage

1. **Upload Files**
   - Click the upload button or drag & drop Excel files
   - Supported formats: XLSX, XLS, CSV
   - Maximum file size: 10MB

2. **Create Visualizations**
   - Select a file from the list
   - Choose columns for X and Y axes
   - Select a chart type:
     - Line: For trend analysis
     - Bar: For comparison
     - Pie: For composition
     - Scatter: For correlation
     - Heatmap: For density
     - Box: For distribution
     - Violin: For probability density
   - Customize appearance with color picker
   - Use reset button to start over

3. **Analyze Data**
   - View basic statistics
   - Calculate probabilities
   - Export results
   - Copy values to clipboard

## 🔧 Troubleshooting

1. **File Upload Issues**
   ```bash
   # Check file permissions
   chmod 755 media/
   ```

2. **Chart Display Problems**
   - Clear browser cache
   - Check console for errors
   - Verify data format

3. **Database Issues**
   ```bash
   # Reset database
   python manage.py flush
   python manage.py migrate
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.