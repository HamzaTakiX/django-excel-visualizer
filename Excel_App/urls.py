"""
URL Configuration for Excel_App

This module defines the URL patterns for the Excel Visualization application.
Each path maps to a specific view function that handles the corresponding HTTP request.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Main landing page is now the upload page
    path('', views.upload_excel, name='upload_excel'),
    
    # Files list view moved to /files/
    path('files/', views.excel_list, name='excel_list'),
    
    # Visualization and data handling
    path('visualize/<int:file_index>/', views.visualize_page, name='visualize_page'),
    path('get_file_data/<int:file_index>/', views.get_file_data, name='get_file_data'),
    path('save_file_data/<int:file_index>/', views.save_file_data, name='save_file_data'),
    path('probability/', views.probability_page, name='probability'),
    path('probability/<str:distribution_type>/', views.probability_calc, name='probability_calc'),
    path('get_file_columns/<int:file_id>/', views.get_file_columns, name='get_file_columns'),
    path('calculate_probability/', views.calculate_probability, name='calculate_probability'),
    
    # Graphs
    path('graphs/', views.graphs_page, name='graphs'),
    path('create_graph/', views.create_graph_page, name='create_graph'),
    path('api/upload_file/', views.upload_file, name='upload_file'),
    path('api/create_graph/', views.create_graph, name='create_graph_api'),
    
    # File operations
    path('delete-file/<int:file_index>/', views.delete_single_excel, name='delete_single_excel'),
    path('delete-multiple/', views.delete_multiple_excel, name='delete_multiple_excel'),
    path('delete-all/', views.delete_all_files, name='delete_all_files'),
    path('download/<int:file_index>/', views.download_file, name='download_file'),
    path('save_changes/<int:file_index>/', views.save_changes, name='save_changes'),
    
    # New endpoint for getting all file IDs
    path('get-all-file-ids/', views.get_all_file_ids, name='get_all_file_ids'),
]
