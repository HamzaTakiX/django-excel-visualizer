from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
import pandas as pd
import os
from .models import ExcelFile
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from django.conf import settings
import numpy as np
from scipy.stats import binom, poisson, norm, bernoulli, uniform, expon


def handle_uploaded_file(file):
    """
    Process an uploaded Excel file and extract its information.
    """
    try:
        # Determine file extension
        file_ext = os.path.splitext(file.name)[1].lower()
        
        # Choose engine based on file extension
        if file_ext == '.xlsx':
            engine = 'openpyxl'
        elif file_ext == '.xls':
            engine = 'xlrd'
        elif file_ext == '.ods':
            engine = 'odf'
        else:
            engine = 'openpyxl'  # default
            
        # Read only the first few rows to get column info
        df_sample = pd.read_excel(file, engine=engine, nrows=5)
        columns_count = len(df_sample.columns)
        
        # Reset file pointer
        file.seek(0)
        
        # Get row count without loading entire file
        rows_count = sum(1 for row in pd.read_excel(file, engine=engine, chunksize=1000))
        
        file_info = {
            'rows_count': rows_count,
            'columns_count': columns_count,
            'file_size': file.size,
        }
        
        return file_info, df_sample.to_json()
        
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
                # Unknown extension, try all methods
                try:
                    df = pd.read_excel(file_path, engine='openpyxl')
                except Exception:
                    try:
                        df = pd.read_excel(file_path, engine='xlrd')
                    except Exception:
                        try:
                            df = pd.read_csv(file_path)
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
            if file_ext in ['.xlsx', '.xls']:
                df.to_excel(excel_file.file.path, index=False, engine='xlsxwriter')
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

@require_http_methods(["POST", "GET"])
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
        filename = os.path.splitext(excel_file.file_name)[0]
        
        # Get data from POST request if available, otherwise read from file
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                df = pd.DataFrame(data.get('data', []))
            except (json.JSONDecodeError, KeyError):
                return JsonResponse({'error': 'Invalid data format'}, status=400)
        else:
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
            if file_ext in ['.xlsx', '.xls']:
                print("Saving as Excel with xlsxwriter...")
                df.to_excel(file_path, index=False, engine='xlsxwriter')
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

def read_file_with_pandas(file_path):
    """
    Try to read a file using different pandas readers and engines.
    """
    try:
        # Try reading as Excel with openpyxl
        return pd.read_excel(file_path, engine='openpyxl')
    except Exception as e1:
        try:
            # Try reading as Excel with xlrd
            return pd.read_excel(file_path, engine='xlrd')
        except Exception as e2:
            try:
                # Try reading as CSV
                return pd.read_csv(file_path)
            except Exception as e3:
                try:
                    # Try reading as Excel without specifying engine
                    return pd.read_excel(file_path)
                except Exception as e4:
                    raise ValueError(f"Could not read file. Tried multiple formats:\nopenpyxl: {str(e1)}\nxlrd: {str(e2)}\ncsv: {str(e3)}\ndefault: {str(e4)}")

def get_file_columns(request, file_id):
    """
    API endpoint to get columns from a file.
    Returns both numeric and categorical columns with their types.
    """
    try:
        graph_type = request.GET.get('graph_type', 'line')
        excel_file = ExcelFile.objects.get(id=file_id)
        file_path = excel_file.file.path
        
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Get numeric columns
            numeric_dtypes = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
            numeric_columns = df.select_dtypes(include=numeric_dtypes).columns.tolist()
            
            # Get categorical columns - include both object and any column with less than 50% unique values
            categorical_columns = []
            for col in df.columns:
                if col not in numeric_columns:
                    # If it's already an object/category type, or if it has low cardinality
                    if df[col].dtype == 'object' or df[col].dtype.name == 'category' or \
                       (len(df[col].unique()) / len(df[col]) < 0.5 and len(df[col].unique()) > 1):
                        categorical_columns.append(col)
            
            # For box plots and some other types, we only want numeric columns
            if graph_type in ['scatter', 'line']:
                columns = numeric_columns
            elif graph_type == 'box':
                # For box plots, allow both types for x-axis but only numeric for y-axis
                columns = numeric_columns + categorical_columns
            else:
                # For bar, pie charts etc, we can use both numeric and categorical
                columns = numeric_columns + categorical_columns
            
            # Print debug info
            print(f"File: {file_path}")
            print(f"All columns: {df.columns.tolist()}")
            print(f"Column types: {df.dtypes.to_dict()}")
            print(f"Numeric columns: {numeric_columns}")
            print(f"Categorical columns: {categorical_columns}")
            
            return JsonResponse({
                'columns': columns,
                'numeric_columns': numeric_columns,
                'categorical_columns': categorical_columns,
                'total_columns': len(df.columns)
            })
            
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return JsonResponse({'error': f'Error reading file: {str(e)}'}, status=400)
            
    except ExcelFile.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def calculate_probability(request):
    """
    Calculate probability based on the selected distribution and parameters.
    """
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        columns = [str(col) for col in data.get('columns', [])]  # Convert column names to strings
        distribution_type = data.get('distribution_type')

        if not file_id or not columns or not distribution_type:
            return JsonResponse({'error': 'Missing required parameters'}, status=400)

        excel_file = ExcelFile.objects.get(id=file_id)
        df = read_file_with_pandas(excel_file.file.path)
        
        # Convert DataFrame column names to strings
        df.columns = df.columns.astype(str)
        
        # Ensure columns exist in the DataFrame
        missing_columns = [col for col in columns if col not in df.columns]
        if missing_columns:
            return JsonResponse({
                'error': f'Colonnes non trouvées: {", ".join(missing_columns)}'
            }, status=400)

        # Convert selected columns to a single Pandas Series and handle non-numeric values
        data_series = pd.Series()
        for col in columns:
            # Convert column to numeric, coerce errors to NaN
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            # Append non-NaN values to data_series
            data_series = pd.concat([data_series, numeric_col.dropna()])

        if len(data_series) == 0:
            return JsonResponse({
                'error': 'Aucune donnée numérique valide trouvée dans les colonnes sélectionnées'
            }, status=400)

        # Convert to numpy array for calculations
        data_array = data_series.to_numpy()

        # Calculate basic statistics
        data_mean = np.mean(data_array)
        data_std = np.std(data_array, ddof=1)  # ddof=1 for sample standard deviation
        observation_count = len(data_array)

        result = {
            'probability': 0,
            'confidence_interval': [0, 0],
            'data': {'x': [], 'y': []},
            'observation_count': observation_count,
            'data_mean': float(data_mean),
            'data_std': float(data_std),
            'distribution_params': {}
        }

        if distribution_type == 'binomial':
            n = int(data.get('n', 10))
            p = float(data.get('p', 0.5))
            
            # Calculate probability
            k = len(data_array[data_array > 0])  # number of successes
            result['probability'] = float(binom.pmf(k, n, p))
            result['distribution_params'] = {
                'n (nombre d\'essais)': n,
                'p (probabilité de succès)': p,
                'k (succès observés)': k
            }
            
            # Calculate confidence interval
            ci = binom.interval(0.95, n, p)
            result['confidence_interval'] = [float(ci[0]), float(ci[1])]
            
            # Generate distribution plot data
            x = np.arange(0, n+1)
            y = binom.pmf(x, n, p)
            result['data'] = {'x': x.tolist(), 'y': y.tolist()}

        elif distribution_type == 'poisson':
            lambda_param = float(data.get('lambda', 1.0))
            
            # Calculate probability
            k = int(data_mean)
            result['probability'] = float(poisson.pmf(k, lambda_param))
            result['distribution_params'] = {
                'λ (lambda)': lambda_param,
                'k (événements observés)': k
            }
            
            # Calculate confidence interval
            ci = poisson.interval(0.95, lambda_param)
            result['confidence_interval'] = [float(ci[0]), float(ci[1])]
            
            # Generate distribution plot data
            x = np.arange(0, int(lambda_param * 3))
            y = poisson.pmf(x, lambda_param)
            result['data'] = {'x': x.tolist(), 'y': y.tolist()}

        elif distribution_type == 'normal':
            mean = float(data.get('mean', 0))
            std = float(data.get('std', 1))
            
            # Calculate probability (probability of being within 1 std dev of mean)
            result['probability'] = float(norm.cdf(mean + std, mean, std) - norm.cdf(mean - std, mean, std))
            result['distribution_params'] = {
                'μ (moyenne)': mean,
                'σ (écart-type)': std
            }
            
            # Calculate confidence interval
            ci = norm.interval(0.95, mean, std)
            result['confidence_interval'] = [float(ci[0]), float(ci[1])]
            
            # Generate distribution plot data
            x = np.linspace(mean - 4*std, mean + 4*std, 100)
            y = norm.pdf(x, mean, std)
            result['data'] = {'x': x.tolist(), 'y': y.tolist()}

        elif distribution_type == 'bernoulli':
            p = float(data.get('p', 0.5))
            
            # Calculate probability
            k = 1 if data_mean > 0.5 else 0
            result['probability'] = float(bernoulli.pmf(k, p))
            result['distribution_params'] = {
                'p (probabilité de succès)': p,
                'Résultat observé': k
            }
            
            # Calculate confidence interval
            ci = bernoulli.interval(0.95, p)
            result['confidence_interval'] = [float(ci[0]), float(ci[1])]
            
            # Generate distribution plot data
            x = np.array([0, 1])
            y = bernoulli.pmf(x, p)
            result['data'] = {'x': x.tolist(), 'y': y.tolist()}

        elif distribution_type == 'uniform':
            a = float(data.get('a', 0))
            b = float(data.get('b', 1))
            
            # Calculate probability (probability of being in middle third)
            result['probability'] = float(uniform.cdf(b/3*2, a, b) - uniform.cdf(b/3, a, b))
            result['distribution_params'] = {
                'a (borne inférieure)': a,
                'b (borne supérieure)': b
            }
            
            # Calculate confidence interval
            ci = uniform.interval(0.95, a, b)
            result['confidence_interval'] = [float(ci[0]), float(ci[1])]
            
            # Generate distribution plot data
            x = np.linspace(a-0.1*(b-a), b+0.1*(b-a), 100)
            y = uniform.pdf(x, a, b-a)
            result['data'] = {'x': x.tolist(), 'y': y.tolist()}

        elif distribution_type == 'exponential':
            lambda_param = float(data.get('lambda', 1))
            
            # Calculate probability (probability of being less than mean)
            result['probability'] = float(expon.cdf(1/lambda_param, scale=1/lambda_param))
            result['distribution_params'] = {
                'λ (lambda)': lambda_param,
                'Moyenne (1/λ)': 1/lambda_param
            }
            
            # Calculate confidence interval
            ci = expon.interval(0.95, scale=1/lambda_param)
            result['confidence_interval'] = [float(ci[0]), float(ci[1])]
            
            # Generate distribution plot data
            x = np.linspace(0, 5/lambda_param, 100)
            y = expon.pdf(x, scale=1/lambda_param)
            result['data'] = {'x': x.tolist(), 'y': y.tolist()}

        else:
            return JsonResponse({'error': f'Distribution type {distribution_type} not supported'}, status=400)

        return JsonResponse(result)

    except ExcelFile.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)
    except Exception as e:
        print(f"Error calculating probability: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

def probability_page(request):
    """
    Render the probability distribution page.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: Rendered probability template
    """
    return render(request, 'Excel_App/probability.html')

def probability_calc(request, distribution_type):
    """
    Render the probability calculation page for a specific distribution.
    """
    distribution_names = {
        'binomial': 'Distribution Binomiale',
        'poisson': 'Distribution de Poisson',
        'normal': 'Distribution Normale',
        'bernoulli': 'Distribution de Bernoulli',
        'uniform': 'Distribution Uniforme',
        'exponential': 'Distribution Exponentielle'
    }

    excel_files = ExcelFile.objects.all()
    
    context = {
        'distribution_type': distribution_type,
        'distribution_name': distribution_names.get(distribution_type, ''),
        'excel_files': excel_files
    }
    
    return render(request, 'Excel_App/probability_calc.html', context)

def graphs_page(request):
    """
    View function for the graphs page where users can create different types of visualizations.
    """
    return render(request, 'Excel_App/graphs.html')

def create_graph_page(request):
    """
    View function for the graph creation page.
    """
    graph_type = request.GET.get('type', 'line')  # Type par défaut : line
    
    # Récupérer la liste des fichiers depuis la base de données
    excel_files = ExcelFile.objects.all()
    files_list = []
    for file in excel_files:
        files_list.append({
            'id': file.id,  # Use actual database ID
            'name': os.path.basename(file.file.name),
            'path': file.file.path
        })
    
    context = {
        'graph_type': graph_type,
        'excel_files': files_list
    }
    return render(request, 'Excel_App/create_graph.html', context)

def upload_file(request):
    """
    API endpoint for file upload.
    """
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        
        # Lire le fichier avec pandas
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
            
        # Stocker le DataFrame dans la session
        request.session['df_columns'] = df.columns.tolist()
        request.session['file_path'] = file.name
        
        return JsonResponse({'columns': df.columns.tolist()})
    return JsonResponse({'error': 'No file uploaded'}, status=400)

def create_graph(request):
    """
    API endpoint for graph creation.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            file_id = data.get('file_id')
            
            if file_id is None:
                return JsonResponse({'error': 'No file selected'}, status=400)
            
            try:
                excel_file = ExcelFile.objects.get(id=file_id)
            except ExcelFile.DoesNotExist:
                return JsonResponse({'error': 'Invalid file ID'}, status=400)
            
            file_path = excel_file.file.path
                
            # Get parameters
            x_column = data.get('x_column')
            y_column = data.get('y_column')
            graph_type = data.get('graph_type', 'line')
            title = data.get('title', 'Mon graphique')
            color = data.get('color', '#0066ff')
            line_style = data.get('line_style', 'solid')
            
            try:
                # Read the file
                if file_path.endswith('.csv'):
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
                        
                elif file_path.endswith('.xlsx') or file_path.endswith('.xlsm'):
                    df = pd.read_excel(file_path, engine='openpyxl')
                    
                elif file_path.endswith('.xls'):
                    df = pd.read_excel(file_path, engine='xlrd')
                    
                else:
                    # Unknown extension, try all methods
                    try:
                        df = pd.read_excel(file_path, engine='openpyxl')
                    except Exception:
                        try:
                            df = pd.read_excel(file_path, engine='xlrd')
                        except Exception:
                            try:
                                df = pd.read_csv(file_path)
                            except Exception as e:
                                return JsonResponse({'error': 'Unable to read file'}, status=400)
                
                # Validate columns exist
                if x_column not in df.columns:
                    return JsonResponse({'error': f'Column {x_column} not found in file'}, status=400)
                if y_column not in df.columns:
                    return JsonResponse({'error': f'Column {y_column} not found in file'}, status=400)
                
                # Handle bar graph
                if graph_type == 'bar':
                    # For bar graphs, we can use categorical data
                    # Count occurrences if y is categorical, otherwise sum numeric values
                    if pd.api.types.is_numeric_dtype(df[y_column]):
                        # If y is numeric, sum the values
                        bar_data = df.groupby(x_column)[y_column].sum().reset_index()
                    else:
                        # If y is categorical, count occurrences
                        bar_data = df.groupby(x_column).size().reset_index(name=y_column)
                    
                    if bar_data.empty:
                        return JsonResponse({'error': 'No valid data points'}, status=400)
                    
                    # Create bar trace
                    trace = {
                        'type': 'bar',
                        'x': bar_data[x_column].tolist(),
                        'y': bar_data[y_column].tolist(),
                        'name': y_column,
                        'marker': {'color': color}
                    }
                    
                    # Add axis titles
                    layout = {
                        'title': {'text': title},
                        'showlegend': True,
                        'template': 'plotly_white',
                        'xaxis': {'title': {'text': x_column}},
                        'yaxis': {'title': {'text': y_column if pd.api.types.is_numeric_dtype(df[y_column]) else 'Count'}}
                    }

                # Handle pie chart
                elif graph_type == 'pie':
                    df[y_column] = pd.to_numeric(df[y_column], errors='coerce')
                    df = df.dropna(subset=[y_column])
                    pie_data = df.groupby(x_column)[y_column].sum()
                    
                    trace = {
                        'type': 'pie',
                        'labels': pie_data.index.tolist(),
                        'values': pie_data.values.tolist(),
                        'name': y_column,
                        'marker': {'colors': [color]}
                    }
                    
                    layout = {
                        'title': {'text': title},
                        'showlegend': True,
                        'template': 'plotly_white'
                    }

                # Handle box plot
                elif graph_type == 'box':
                    # Convert only y-column to numeric (x can be categorical)
                    df[y_column] = pd.to_numeric(df[y_column], errors='coerce')
                    df = df.dropna(subset=[y_column])
                    
                    if df.empty:
                        return JsonResponse({'error': 'No valid numeric data points for y-axis'}, status=400)
                    
                    # Create box plot trace
                    trace = {
                        'type': 'box',
                        'x': df[x_column].tolist(),
                        'y': df[y_column].tolist(),
                        'name': y_column,
                        'marker': {'color': color}
                    }
                    
                    layout = {
                        'title': {'text': title},
                        'showlegend': True,
                        'template': 'plotly_white',
                        'xaxis': {'title': {'text': x_column}},
                        'yaxis': {'title': {'text': y_column}}
                    }
                    
                # Handle scatter plot
                elif graph_type == 'scatter':
                    # Convert both columns to numeric
                    df[x_column] = pd.to_numeric(df[x_column], errors='coerce')
                    df[y_column] = pd.to_numeric(df[y_column], errors='coerce')
                    df = df.dropna(subset=[x_column, y_column])
                    
                    if df.empty:
                        return JsonResponse({'error': 'No valid numeric data points'}, status=400)
                    
                    trace = {
                        'type': 'scatter',
                        'mode': 'markers',  # This is crucial for scatter plots
                        'x': df[x_column].tolist(),
                        'y': df[y_column].tolist(),
                        'name': y_column,
                        'marker': {
                            'color': color,
                            'size': 8,
                            'opacity': 0.7
                        }
                    }
                    
                    layout = {
                        'title': {'text': title},
                        'showlegend': True,
                        'template': 'plotly_white',
                        'xaxis': {'title': {'text': x_column}},
                        'yaxis': {'title': {'text': y_column}}
                    }
                    
                # Handle heatmap
                elif graph_type == 'heatmap':
                    try:
                        # Convert both columns to numeric
                        df[x_column] = pd.to_numeric(df[x_column], errors='coerce')
                        df[y_column] = pd.to_numeric(df[y_column], errors='coerce')
                        df = df.dropna(subset=[x_column, y_column])
                        
                        if df.empty:
                            return JsonResponse({'error': 'No valid numeric data points'}, status=400)
                        
                        # Create bins for both axes
                        x_bins = pd.qcut(df[x_column], q=10, duplicates='drop')  # Create 10 quantile bins
                        y_bins = pd.qcut(df[y_column], q=10, duplicates='drop')  # Create 10 quantile bins
                        
                        # Create a 2D histogram
                        heatmap_data = pd.crosstab(y_bins, x_bins)
                        
                        # Create the heatmap trace
                        trace = {
                            'type': 'heatmap',
                            'z': heatmap_data.values.tolist(),  # 2D array of values
                            'x': [f'{x:.2f}' for x in heatmap_data.columns.categories.mid],  # X-axis labels
                            'y': [f'{y:.2f}' for y in heatmap_data.index.categories.mid],    # Y-axis labels
                            'colorscale': 'Viridis',
                            'showscale': True,
                            'hoverongaps': False
                        }
                        
                        layout = {
                            'title': {'text': title},
                            'showlegend': False,
                            'template': 'plotly_white',
                            'xaxis': {
                                'title': {'text': x_column},
                                'side': 'bottom'
                            },
                            'yaxis': {
                                'title': {'text': y_column},
                                'autorange': 'reversed'  # This makes the heatmap display correctly
                            },
                            'coloraxis': {
                                'colorbar': {
                                    'title': 'Count',
                                    'thickness': 20,
                                    'len': 0.7
                                }
                            }
                        }
                    except Exception as e:
                        return JsonResponse({'error': f'Error creating heatmap: {str(e)}'}, status=400)
                    
                # Handle other chart types
                else:
                    df[x_column] = pd.to_numeric(df[x_column], errors='coerce')
                    df[y_column] = pd.to_numeric(df[y_column], errors='coerce')
                    df = df.dropna(subset=[x_column, y_column])
                    
                    if df.empty:
                        return JsonResponse({'error': 'No valid numeric data points'}, status=400)
                    
                    trace = {
                        'type': graph_type,
                        'x': df[x_column].tolist(),
                        'y': df[y_column].tolist(),
                        'name': y_column
                    }
                    
                    if graph_type == 'line':
                        trace['line'] = {'color': color, 'dash': line_style}
                    else:
                        trace['marker'] = {'color': color}
                    
                    layout = {
                        'title': {'text': title},
                        'showlegend': True,
                        'template': 'plotly_white',
                        'xaxis': {'title': {'text': x_column}},
                        'yaxis': {'title': {'text': y_column}}
                    }
                
                # Create the final graph data structure
                graph_data = {
                    'data': [trace],
                    'layout': layout
                }
                
                return JsonResponse({'graph': graph_data})
                
            except Exception as e:
                return JsonResponse({'error': f'Error creating graph: {str(e)}'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def create_bar_graph(request):
    """
    API endpoint for bar graph creation.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            file_id = data.get('file_id')
            
            if file_id is None:
                return JsonResponse({'error': 'No file selected'}, status=400)
            
            # Get file by ID from database
            try:
                excel_file = ExcelFile.objects.get(id=file_id)
            except ExcelFile.DoesNotExist:
                return JsonResponse({'error': 'Invalid file ID'}, status=400)
            
            file_path = excel_file.file.path
                
            # Get parameters
            x_column = data.get('x_column')
            y_column = data.get('y_column')
            title = data.get('title', 'Mon graphique')
            color = data.get('color', '#0066ff')
            
            try:
                if file_path.endswith('.csv'):
                    # Try different encodings for CSV
                    encodings = ['utf-8', 'latin1', 'cp1252']
                    df = None
                    last_error = None
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                        except Exception as e:
                            last_error = str(e)
                        
                elif file_path.endswith('.xlsx') or file_path.endswith('.xlsm'):
                    df = pd.read_excel(file_path, engine='openpyxl')
                    
                elif file_path.endswith('.xls'):
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
                                return JsonResponse({'error': 'Unable to read file'}, status=400)
                
                # Validate columns exist
                if x_column not in df.columns:
                    return JsonResponse({'error': f'Column {x_column} not found in file'}, status=400)
                if y_column not in df.columns:
                    return JsonResponse({'error': f'Column {y_column} not found in file'}, status=400)
                
                # For bar graphs, we can use categorical data
                # Count occurrences if y is categorical, otherwise sum numeric values
                if pd.api.types.is_numeric_dtype(df[y_column]):
                    # If y is numeric, sum the values
                    bar_data = df.groupby(x_column)[y_column].sum().reset_index()
                else:
                    # If y is categorical, count occurrences
                    bar_data = df.groupby(x_column).size().reset_index(name=y_column)
                
                if bar_data.empty:
                    return JsonResponse({'error': 'No valid data points'}, status=400)
                
                trace = {
                    'type': 'bar',
                    'x': bar_data[x_column].tolist(),
                    'y': bar_data[y_column].tolist(),
                    'name': y_column,
                    'marker': {
                        'color': color
                    }
                }
                
                layout = {
                    'title': title,
                    'showlegend': True,
                    'template': 'plotly_white',
                    'xaxis': {'title': {'text': x_column}},
                    'yaxis': {'title': {'text': y_column if pd.api.types.is_numeric_dtype(df[y_column]) else 'Count'}}
                }
                
                graph_data = {
                    'data': [trace],
                    'layout': layout
                }
                
                return JsonResponse({'graph': graph_data})
                
            except Exception as e:
                return JsonResponse({'error': f'Error creating graph: {str(e)}'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
