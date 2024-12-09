"""
Main views file for the Excel Visualization Application.
This file contains all the view functions that handle different routes and functionalities
of the application, including file upload, visualization, and management operations.
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
import pandas as pd
import os
from datetime import datetime
import pytz
from django.utils import timezone
from .models import ExcelFile
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from django.conf import settings

def handle_uploaded_file(file):
    """
    Process an uploaded Excel file and extract its information.
    
    Args:
        file: The uploaded file object from the request
        
    Returns:
        tuple: (file_info, df_json) where:
            - file_info: Dictionary containing file metadata
            - df_json: JSON representation of the Excel data
            
    Raises:
        Exception: If there's an error processing the file
    """
    try:
        # Try reading with different Excel engines
        try:
            # Try openpyxl first (for .xlsx files)
            df = pd.read_excel(file, engine='openpyxl')
        except:
            try:
                # Try xlrd as fallback (for .xls files)
                df = pd.read_excel(file, engine='xlrd')
            except:
                # Try odf as another fallback (for .ods files)
                df = pd.read_excel(file, engine='odf')
        
        # Store the DataFrame in session as JSON
        df_json = df.to_json()
        
        # Get file information
        file_info = {
            'file_name': file.name,
            'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'rows': len(df),
            'columns': len(df.columns),
            'file_size': f"{file.size / 1024:.2f} KB",
            'preview': df.head().to_html(classes=['table', 'table-striped', 'table-hover'], index=False)
        }
        
        return file_info, df_json
    except Exception as e:
        raise Exception(f"Error processing file: {str(e)}")

def upload_excel(request):
    if request.method == 'POST':
        files = request.FILES.getlist('excel_file')
        if not files:
            messages.error(request, 'Please select at least one file to upload')
            return render(request, 'Excel_App/upload.html')
        
        success_count = 0
        error_files = []
        
        for excel_file in files:
            file_size_mb = excel_file.size / (1024 * 1024)  # Convert to MB
            
            # Check file size (limit to 10MB)
            if file_size_mb > 10:
                error_files.append(f"{excel_file.name}: File too large ({file_size_mb:.1f}MB). Maximum size is 10MB")
                continue
                
            try:
                df = None
                success = False
                last_error = None
                file_ext = excel_file.name.lower().split('.')[-1] if '.' in excel_file.name else ''
                
                # Try different methods based on file extension
                if file_ext == 'xlsx' or file_ext == 'xlsm':
                    try:
                        # Force openpyxl for .xlsx files
                        df = pd.read_excel(excel_file, engine='openpyxl')
                        success = True
                    except Exception as e:
                        print(f"Error reading .xlsx with openpyxl: {str(e)}")
                        last_error = str(e)
                
                elif file_ext == 'xls':
                    try:
                        # Force xlrd for .xls files
                        df = pd.read_excel(excel_file, engine='xlrd')
                        success = True
                    except Exception as e:
                        print(f"Error reading .xls with xlrd: {str(e)}")
                        last_error = str(e)
                
                elif file_ext == 'csv':
                    try:
                        # Try different encodings for CSV
                        encodings = ['utf-8', 'latin1', 'cp1252']
                        for encoding in encodings:
                            try:
                                df = pd.read_csv(excel_file, encoding=encoding)
                                success = True
                                break
                            except UnicodeDecodeError:
                                continue
                            except Exception as e:
                                last_error = str(e)
                    except Exception as e:
                        print(f"Error reading CSV: {str(e)}")
                        last_error = str(e)
                
                else:
                    # Unknown extension, try all methods
                    try:
                        df = pd.read_excel(excel_file, engine='openpyxl')
                        success = True
                    except Exception as e1:
                        try:
                            df = pd.read_excel(excel_file, engine='xlrd')
                            success = True
                        except Exception as e2:
                            try:
                                df = pd.read_csv(excel_file)
                                success = True
                            except Exception as e3:
                                last_error = f"Tried multiple formats. Last error: {str(e3)}"

                if not success or df is None:
                    error_message = f"Unable to read file. Error: {last_error}"
                    print(f"File {excel_file.name}: {error_message}")
                    error_files.append(f"{excel_file.name}: {error_message}")
                    continue

                # Check if file is empty
                if df.empty:
                    error_files.append(f"{excel_file.name}: File is empty")
                    continue
                    
                # Check if file has too many rows (limit to 100,000 rows)
                if len(df) > 100000:
                    error_files.append(f"{excel_file.name}: Too many rows ({len(df):,}). Maximum is 100,000 rows")
                    continue
                    
                # Save the file with row and column counts
                excel_instance = ExcelFile(
                    file=excel_file,
                    file_name=excel_file.name,
                    rows_count=len(df),
                    columns_count=len(df.columns)
                )
                excel_instance.save()
                success_count += 1
                
            except Exception as e:
                error_message = str(e)
                print(f"Final error for {excel_file.name}: {error_message}")
                error_files.append(f"{excel_file.name}: Error processing file - {error_message}")
        
        # Show a single success message for all uploaded files
        if success_count > 0:
            if success_count == 1:
                messages.success(request, '1 file uploaded successfully!')
            else:
                messages.success(request, f'{success_count} files uploaded successfully!')
        
        # Show error messages for failed uploads
        for error in error_files:
            messages.error(request, error)
            print(f"Error message sent to user: {error}")
        
        return redirect('excel_list')
    
    return render(request, 'Excel_App/upload.html')

def excel_list(request):
    """
    Display a list of all uploaded Excel files.
    Files can be sorted by name, date, or size.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered template with sorted list of Excel files
    """
    sort_param = request.GET.get('sort', 'date_desc')
    excel_files = ExcelFile.objects.all()
    
    # Sorting logic based on parameters
    if sort_param == 'name_asc':
        excel_files = excel_files.order_by('file_name')
    elif sort_param == 'name_desc':
        excel_files = excel_files.order_by('-file_name')
    elif sort_param == 'date_asc':
        excel_files = excel_files.order_by('uploaded_at')
    elif sort_param == 'date_desc':
        excel_files = excel_files.order_by('-uploaded_at')
    elif sort_param == 'size_asc':
        excel_files = excel_files.order_by('file_size')
    elif sort_param == 'size_desc':
        excel_files = excel_files.order_by('-file_size')

    # Pagination
    paginator = Paginator(excel_files, 6)  # Show 6 files per page
    page = request.GET.get('page', 1)
    
    try:
        files_page = paginator.page(page)
    except PageNotAnInteger:
        files_page = paginator.page(1)
    except EmptyPage:
        files_page = paginator.page(paginator.num_pages)

    return render(request, 'Excel_App/excel_list.html', {
        'excel_files': files_page,
        'current_sort': sort_param,
        'page_obj': files_page,  # Add this for pagination template
    })

def view_excel(request, file_index):
    """
    Display the contents of a specific Excel file.
    Converts the Excel data to an HTML table for viewing.
    
    Args:
        request: HTTP request object
        file_index: ID of the Excel file to view
        
    Returns:
        HttpResponse: Rendered template with Excel data or redirect on error
    """
    try:
        excel_file = ExcelFile.objects.get(id=file_index)
        df = pd.read_excel(excel_file.file.path)
        columns = df.columns.tolist()
        table_html = df.to_html(classes=['table', 'table-striped', 'table-hover'], 
                              index=False, escape=False)
        excel_file.preview_data = table_html
        
        context = {
            'excel_file': excel_file,
            'has_data': True,
            'error_message': None,
            'columns': columns,
            'file_index': file_index
        }
        
        return render(request, 'Excel_App/visualize.html', context)
            
    except Exception as e:
        messages.error(request, f'Error viewing file: {str(e)}')
    
    return redirect('excel_list')

def visualize_excel(request, file_index):
    """
    Generate visualizations for Excel file data.
    Handles data formatting and prepares it for various chart types.
    
    Args:
        request: HTTP request object
        file_index: ID of the Excel file to visualize
        
    Returns:
        HttpResponse: Rendered template with visualization options
    """
    try:
        # Get the Excel file by ID
        excel_file = ExcelFile.objects.get(id=file_index)
        
        # Read the Excel file using pandas
        df = pd.read_excel(excel_file.file.path)
        
        # Format numeric columns to 2 decimal places
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_columns:
            df[col] = df[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else '')
        
        # Generate HTML table with bootstrap classes
        preview_data = df.to_html(
            classes=['table', 'table-striped', 'table-hover'],
            index=False,
            na_rep='N/A',
            escape=False,
            float_format=None  # We already formatted numeric columns
        )
        
        # Calculate file size in a readable format
        file_size = excel_file.file.size
        if file_size < 1024:
            file_size_display = f"{file_size} B"
        elif file_size < 1024 * 1024:
            file_size_display = f"{file_size/1024:.1f} KB"
        else:
            file_size_display = f"{file_size/(1024*1024):.1f} MB"
        
        # Add file size display method to excel_file object
        excel_file.get_file_size_display = lambda: file_size_display
        
        context = {
            'excel_file': excel_file,
            'has_data': len(df) > 0,
            'preview_data': preview_data,
        }
        
        return render(request, 'Excel_App/visualize.html', context)
        
    except ExcelFile.DoesNotExist:
        messages.error(request, 'Excel file not found.')
        return redirect('excel_list')
    except Exception as e:
        messages.error(request, f'Error visualizing file: {str(e)}')
        return redirect('excel_list')

def download_csv(request, file_index):
    try:
        # Get the Excel file
        excel_file = ExcelFile.objects.get(id=file_index)
        file_path = os.path.join(settings.MEDIA_ROOT, str(excel_file.file))
        
        # Read the file with pandas
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            try:
                df = pd.read_excel(file_path, engine='xlrd')
            except Exception as e:
                return JsonResponse({
                    'error': 'Could not read the Excel file. Please ensure it is not corrupted.'
                }, status=400)

        # Create a response with CSV content
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{os.path.splitext(excel_file.file_name)[0]}.csv"'
        
        # Convert DataFrame to CSV
        df.to_csv(response, index=False, encoding='utf-8')
        
        return response

    except ExcelFile.DoesNotExist:
        return JsonResponse({
            'error': 'File not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'Error downloading file: {str(e)}'
        }, status=500)

def delete_single_excel(request, file_index):
    """View for deleting a single Excel file."""
    try:
        # Get total count of files before deletion
        total_files = ExcelFile.objects.count()
        
        excel_file = ExcelFile.objects.get(id=file_index)
        file_name = excel_file.file_name
        
        # Delete the actual file from storage
        if os.path.exists(excel_file.file.path):
            os.remove(excel_file.file.path)
        excel_file.delete()
        
        # Check if this was the last file
        all_deleted = total_files == 1
        success_message = f'Successfully deleted {file_name}'
        
        if all_deleted:
            # Store the message in session for display after reload
            messages.success(request, success_message)
        
        return JsonResponse({
            'status': 'success',
            'message': success_message,
            'all_deleted': all_deleted
        })
    except ExcelFile.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'File not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_http_methods(["POST"])
def delete_multiple_excel(request):
    """View for deleting multiple Excel files."""
    try:
        data = json.loads(request.body)
        file_ids = data.get('file_ids', [])
        
        if not file_ids:
            return JsonResponse({'status': 'error', 'message': 'No files selected'}, status=400)

        # Get total count of files before deletion
        total_files = ExcelFile.objects.count()
        
        deleted_count = 0
        deleted_ids = []
        for file_id in file_ids:
            try:
                excel_file = ExcelFile.objects.get(id=file_id)
                # Delete the actual file from storage
                if os.path.exists(excel_file.file.path):
                    os.remove(excel_file.file.path)
                excel_file.delete()
                deleted_count += 1
                deleted_ids.append(file_id)
            except ExcelFile.DoesNotExist:
                continue
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error deleting file {file_id}: {str(e)}'
                }, status=500)

        if deleted_count == 0:
            return JsonResponse({
                'status': 'error',
                'message': 'No files were deleted'
            }, status=400)
        
        # Check if all files were deleted
        all_deleted = deleted_count == total_files
        success_message = f'Successfully deleted {deleted_count} files'
        
        if all_deleted:
            # Store the message in session for display after reload
            messages.success(request, success_message)
        
        return JsonResponse({
            'status': 'success',
            'message': success_message,
            'deleted_count': deleted_count,
            'deleted_ids': deleted_ids,
            'all_deleted': all_deleted
        })
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error during bulk delete: {str(e)}'
        }, status=500)

def delete_all_files(request):
    """
    Delete all Excel files from the database and storage.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Redirect to excel_list
    """
    if request.method == 'POST':
        try:
            ExcelFile.objects.all().delete()
            messages.success(request, 'All files deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting files: {str(e)}')
    return redirect('excel_list')

@require_http_methods(["GET"])
def visualize_page(request, file_index):
    """
    Render the Excel file visualization page.
    
    Args:
        request: HTTP request object
        file_index: ID of the Excel file to visualize
        
    Returns:
        HttpResponse: Rendered visualization template
    """
    try:
        excel_file = ExcelFile.objects.get(id=file_index)
        file_path = excel_file.file.path
        
        # Determine file type and read accordingly
        file_ext = os.path.splitext(file_path)[1].lower()
        df = None
        
        if file_ext == '.csv':
            # Try different encodings for CSV
            encodings = ['utf-8', 'latin1', 'cp1252']
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    last_error = str(e)
        
        elif file_ext == '.xlsx' or file_ext == '.xlsm':
            df = pd.read_excel(file_path, engine='openpyxl')
            
        elif file_ext == '.xls':
            df = pd.read_excel(file_path, engine='xlrd')
            
        else:
            # Try all methods
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
            except Exception:
                try:
                    df = pd.read_excel(file_path, engine='xlrd')
                except Exception:
                    try:
                        df = pd.read_csv(file_path)
                    except Exception as e:
                        raise Exception('Unable to read file. Please ensure it is a valid Excel or CSV file.')
        
        if df is None:
            raise Exception('Unable to read file. Please ensure it is a valid Excel or CSV file.')
        
        # Get basic file info
        file_info = {
            'file_name': excel_file.file_name,
            'file_size': excel_file.get_file_size_display(),
            'upload_time': excel_file.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
            'last_modified': excel_file.last_modified.strftime('%Y-%m-%d %H:%M:%S') if excel_file.has_been_edited else None,
            'rows_count': len(df),
            'columns_count': len(df.columns)
        }
        
        # Pass data to template
        context = {
            'file': excel_file,
            'file_index': file_index,
            'data': {
                'file_name': excel_file.file_name,
                'file_size': excel_file.get_file_size_display(),
                'upload_time': excel_file.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                'last_modified': excel_file.last_modified.strftime('%Y-%m-%d %H:%M:%S') if excel_file.has_been_edited else None,
                'rows_count': len(df),
                'columns_count': len(df.columns),
                'columns': df.columns.tolist(),
                'values': df.values.tolist()
            },
            'stats_columns': ['Column Name', 'Data Type', 'Non-Null Count', 'Null Count', 'Mean', 'Median', 'Mode', 'Min', 'Max', 'Std Dev']
        }
        
        return render(request, 'Excel_App/visualize.html', context)
        
    except ExcelFile.DoesNotExist:
        messages.error(request, 'File not found')
        return redirect('excel_list')
    except Exception as e:
        messages.error(request, f'Error loading file: {str(e)}')
        return redirect('excel_list')

@require_http_methods(["GET"])
def get_file_data(request, file_index):
    """
    Get Excel file data and metadata.
    """
    try:
        # Get the Excel file
        excel_file = ExcelFile.objects.get(id=file_index)
        file_path = os.path.join(settings.MEDIA_ROOT, str(excel_file.file))
        
        if not os.path.exists(file_path):
            return JsonResponse({
                'success': False,
                'error': 'File not found on disk'
            }, status=404)

        try:
            df = None
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Try reading based on file extension
            if file_ext == '.csv':
                # Try different encodings for CSV
                encodings = ['utf-8', 'latin1', 'cp1252']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, header=None)
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        last_error = str(e)
                        
            elif file_ext == '.xlsx' or file_ext == '.xlsm':
                df = pd.read_excel(file_path, engine='openpyxl', header=None)
                
            elif file_ext == '.xls':
                df = pd.read_excel(file_path, engine='xlrd', header=None)
                
            else:
                # Unknown extension, try all methods
                try:
                    df = pd.read_excel(file_path, engine='openpyxl', header=None)
                except Exception:
                    try:
                        df = pd.read_excel(file_path, engine='xlrd', header=None)
                    except Exception:
                        try:
                            df = pd.read_csv(file_path, header=None)
                        except Exception as e:
                            return JsonResponse({
                                'success': False,
                                'error': 'Unable to read file. Please ensure it is a valid Excel or CSV file.'
                            }, status=400)

            if df is None:
                return JsonResponse({
                    'success': False,
                    'error': 'Unable to read file. Please ensure it is a valid Excel or CSV file.'
                }, status=400)

            # Get the first row as headers
            headers = df.iloc[0].tolist()
            # Remove the header row and set column names
            df = df.iloc[1:]
            df.columns = headers

            # Replace NaN with empty string
            df = df.fillna('')
            
            # Get file info
            file_stat = os.stat(file_path)
            file_info = {
                'fileName': os.path.basename(file_path),
                'fileSize': f"{file_stat.st_size / 1024:.1f} KB",
                'uploadTime': excel_file.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                'rowCount': str(len(df)),
                'columnCount': str(len(df.columns))
            }

            # Format data for the frontend
            response_data = {
                'success': True,
                'data': {
                    'columns': headers,
                    'values': df.values.tolist()
                },
                'file_info': file_info
            }
            
            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error processing file: {str(e)}'
            }, status=400)

    except ExcelFile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'File not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }, status=500)

@require_http_methods(["POST"])
def save_file_data(request, file_index):
    """
    Save changes made to Excel file data.
    
    Args:
        request: HTTP request object with JSON content
        file_index: ID of the Excel file
        
    Returns:
        JsonResponse: Success/failure status
    """
    try:
        # Get the Excel file object
        excel_file = ExcelFile.objects.get(id=file_index)
        
        # Parse the JSON data from request
        try:
            data = json.loads(request.body)
            content = data.get('content')
            if not content:
                return JsonResponse({
                    'success': False,
                    'error': 'No content provided'
                }, status=400)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        
        # Convert the data to a DataFrame
        try:
            # The data is already in the correct format for DataFrame creation
            df = pd.DataFrame(content)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error converting data: {str(e)}'
            }, status=400)
        
        # Save to Excel file
        try:
            # Get file extension
            file_ext = os.path.splitext(excel_file.file.path)[1].lower()
            
            # Save based on file extension
            if file_ext == '.xlsx':
                df.to_excel(excel_file.file.path, index=False, engine='openpyxl')
            elif file_ext == '.xls':
                df.to_excel(excel_file.file.path, index=False, engine='xlwt')
            else:  # Default to CSV
                df.to_csv(excel_file.file.path, index=False)
            
            # Update file metadata
            excel_file.rows_count = len(df)
            excel_file.columns_count = len(df.columns)
            excel_file.file_size = os.path.getsize(excel_file.file.path)  # Update file size
            excel_file.save(mark_edited=True, update_fields=['rows_count', 'columns_count', 'file_size', 'last_modified', 'has_been_edited'])
            
            # Get the updated last_modified time
            excel_file.refresh_from_db()
            print("File saved successfully")
            
            return JsonResponse({
                'success': True, 
                'message': 'File saved successfully',
                'last_modified': excel_file.last_modified.strftime('%Y-%m-%d %H:%M:%S') if excel_file.has_been_edited else None
            })
            
        except PermissionError as e:
            print(f"Permission error: {str(e)}")
            return JsonResponse({'error': 'Permission denied. Unable to save file'}, status=403)
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return JsonResponse({'error': f'Failed to save changes: {str(e)}'}, status=500)
        
    except ExcelFile.DoesNotExist:
        print("Error: Excel file not found in database")
        return JsonResponse({'error': 'Excel file record not found in database'}, status=404)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)
    finally:
        print("=== End save_changes ===")

@require_http_methods(["GET"])
def download_file(request, file_index):
    """
    Download the Excel file with format conversion.
    
    Args:
        request: HTTP request object
        file_index: ID of the Excel file
        
    Returns:
        FileResponse: Converted file for download
    """
    try:
        # Get the requested format (default to xlsx)
        format = request.GET.get('format', 'xlsx').lower()
        
        # Get the Excel file
        excel_file = ExcelFile.objects.get(id=file_index)
        file_path = excel_file.file.path
        
        if not os.path.exists(file_path):
            return JsonResponse({'error': 'File not found'}, status=404)
            
        # Read the file with pandas
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception:
            try:
                df = pd.read_excel(file_path, engine='xlrd')
            except Exception:
                try:
                    df = pd.read_csv(file_path)
                except Exception:
                    return JsonResponse({'error': 'Unable to read file'}, status=400)
        
        # Create a response with the appropriate content type and conversion
        filename = os.path.splitext(excel_file.file_name)[0]
        
        if format == 'xlsx':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
                
        elif format == 'xls':
            # Create a temporary XLSX file first
            temp_xlsx = os.path.join(settings.MEDIA_ROOT, 'temp', f'{filename}_temp.xlsx')
            os.makedirs(os.path.dirname(temp_xlsx), exist_ok=True)
            df.to_excel(temp_xlsx, index=False, engine='openpyxl')
            
            try:
                # Convert XLSX to XLS using openpyxl and xlwt
                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = f'attachment; filename="{filename}.xls"'
                
                # Use xlwt for XLS format
                import xlwt
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Sheet1')
                
                # Write headers
                for col, header in enumerate(df.columns):
                    ws.write(0, col, str(header))
                
                # Write data
                for row_idx, row in enumerate(df.values, 1):
                    for col_idx, value in enumerate(row):
                        ws.write(row_idx, col_idx, value)
                
                wb.save(response)
                
                # Clean up temporary file
                if os.path.exists(temp_xlsx):
                    os.remove(temp_xlsx)
                    
                return response
                
            except Exception as e:
                # If conversion fails, fallback to XLSX
                if os.path.exists(temp_xlsx):
                    os.remove(temp_xlsx)
                
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
                with pd.ExcelWriter(response, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                    
        elif format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            df.to_csv(response, index=False)
            
        elif format == 'txt':
            response = HttpResponse(content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{filename}.txt"'
            df.to_csv(response, index=False, sep='\t')
            
        elif format == 'json':
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
            df.to_json(response, orient='records', indent=2)
            
        else:
            return JsonResponse({'error': 'Unsupported format'}, status=400)
            
        return response
            
    except ExcelFile.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def save_changes(request, file_index):
    try:
        print("=== Starting save_changes ===")
        print(f"File index: {file_index}")
        
        # Get the Excel file
        excel_file = ExcelFile.objects.get(id=file_index)
        file_path = os.path.join(settings.MEDIA_ROOT, str(excel_file.file))
        print(f"File path: {file_path}")
        
        if not os.path.exists(file_path):
            print("Error: File not found on disk")
            return JsonResponse({'error': 'Excel file not found on the server'}, status=404)
        
        # Get the data from request
        try:
            request_data = json.loads(request.body)
            print("Request data:", request_data)
            data = request_data['data']
            print("Parsed data:", data)
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error parsing request data: {str(e)}")
            return JsonResponse({'error': 'Invalid data format'}, status=400)
        
        if not data:
            print("Error: No data provided")
            return JsonResponse({'error': 'No data provided for saving'}, status=400)
            
        # Convert the data to a DataFrame
        try:
            print("Creating DataFrame...")
            df = pd.DataFrame(data)
            print("DataFrame created successfully")
            print("DataFrame shape:", df.shape)
            print("DataFrame columns:", df.columns.tolist())
        except Exception as e:
            print(f"Error creating DataFrame: {str(e)}")
            return JsonResponse({'error': f'Error converting data: {str(e)}'}, status=400)
        
        # Determine file type and save accordingly
        file_ext = os.path.splitext(file_path)[1].lower()
        try:
            print(f"Saving file with extension: {file_ext}")
            if file_ext == '.xlsx':
                print("Saving as XLSX...")
                df.to_excel(file_path, index=False, engine='openpyxl')
            elif file_ext == '.xls':
                print("Saving as XLS...")
                df.to_excel(file_path, index=False, engine='xlwt')
            else:  # Default to CSV
                print("Saving as CSV...")
                df.to_csv(file_path, index=False)
            
            # Update file metadata and force last_modified update
            excel_file.rows_count = len(df)
            excel_file.columns_count = len(df.columns)
            excel_file.file_size = os.path.getsize(file_path)  # Update file size
            excel_file.save(mark_edited=True, update_fields=['rows_count', 'columns_count', 'file_size', 'last_modified', 'has_been_edited'])
            
            # Get the updated last_modified time
            excel_file.refresh_from_db()
            print("File saved successfully")
            
            return JsonResponse({
                'success': True, 
                'message': 'Changes saved successfully',
                'last_modified': excel_file.last_modified.strftime('%Y-%m-%d %H:%M:%S') if excel_file.has_been_edited else None
            })
            
        except PermissionError as e:
            print(f"Permission error: {str(e)}")
            return JsonResponse({'error': 'Permission denied. Unable to save file'}, status=403)
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return JsonResponse({'error': f'Failed to save changes: {str(e)}'}, status=500)
        
    except ExcelFile.DoesNotExist:
        print("Error: Excel file not found in database")
        return JsonResponse({'error': 'Excel file record not found in database'}, status=404)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)
    finally:
        print("=== End save_changes ===")

@require_http_methods(["GET"])
def get_all_file_ids(request):
    """Get all file IDs for select all functionality"""
    try:
        # Get the sort parameter to maintain consistent order
        sort_param = request.GET.get('sort', 'date_desc')
        excel_files = ExcelFile.objects.all()
        
        # Apply the same sorting as in excel_list view
        if sort_param == 'name_asc':
            excel_files = excel_files.order_by('file_name')
        elif sort_param == 'name_desc':
            excel_files = excel_files.order_by('-file_name')
        elif sort_param == 'date_asc':
            excel_files = excel_files.order_by('uploaded_at')
        elif sort_param == 'date_desc':
            excel_files = excel_files.order_by('-uploaded_at')
        elif sort_param == 'size_asc':
            excel_files = excel_files.order_by('file_size')
        elif sort_param == 'size_desc':
            excel_files = excel_files.order_by('-file_size')
            
        # Get all file IDs in the current sort order
        file_ids = list(excel_files.values_list('id', flat=True))
        return JsonResponse({'file_ids': file_ids})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
