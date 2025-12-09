import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { Document } from '../types';
import { Icons } from '../components/Icons';
import { Spinner } from '../components/ui/Spinner';

export const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = useCallback(async (isBackground = false) => {
    try {
      if (!isBackground) setIsLoading(true);
      const data = await api.get<{ documents: Document[] }>('/documents');
      setDocuments(data.documents);
    } catch (err: any) {
      if (!isBackground) setError('Failed to load documents');
    } finally {
      if (!isBackground) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments(false);
    
    // Poll every 10 seconds to check for new documents
    const interval = setInterval(() => {
      fetchDocuments(true);
    }, 10000);

    return () => clearInterval(interval);
  }, [fetchDocuments]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || event.target.files.length === 0) return;

    setIsUploading(true);
    setError(null);
    const formData = new FormData();
    Array.from(event.target.files).forEach((file) => {
      formData.append('files', file as Blob);
    });

    try {
      await api.postMultipart<{ documents: Document[] }>('/documents/upload', formData);
      await fetchDocuments(false); // Immediate refresh
      // Reset input
      event.target.value = '';
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await api.delete(`/documents/${id}`);
      setDocuments(prev => prev.filter(doc => doc.id !== id));
    } catch (err: any) {
      alert('Failed to delete document');
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="flex-1 h-full overflow-y-auto bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Knowledge Base</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">Manage documents used for context.</p>
          </div>
          <div className="relative group">
            <input
              type="file"
              multiple
              onChange={handleFileUpload}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              disabled={isUploading}
            />
            <button className={`flex items-center px-4 py-2 bg-brand-600 text-white rounded-lg shadow hover:bg-brand-700 transition-colors ${isUploading ? 'opacity-70 cursor-not-allowed' : ''}`}>
              {isUploading ? <Spinner size="sm" className="mr-2 text-white" /> : <Icons.Upload className="w-5 h-5 mr-2" />}
              {isUploading ? 'Uploading...' : 'Upload Documents'}
            </button>
          </div>
        </div>

        {error && (
           <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg relative">
             <span className="block sm:inline">{error}</span>
           </div>
        )}

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
          {isLoading && documents.length === 0 ? (
            <div className="p-12 flex justify-center">
              <Spinner size="lg" />
            </div>
          ) : documents.length === 0 ? (
            <div className="p-12 text-center">
              <Icons.Documents className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">No documents yet</h3>
              <p className="text-gray-500 dark:text-gray-400 mt-1">Upload PDF, TXT, DOCX files to get started.</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Size</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Uploaded</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Chunks</th>
                  <th scope="col" className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center rounded-lg bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400">
                          <Icons.FileText className="w-5 h-5" />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[250px]">{doc.filename}</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase">{doc.content_type.split('/')[1] || 'FILE'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{formatSize(doc.size_bytes)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{new Date(doc.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                          {doc.num_chunks || 0}
                        </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button onClick={() => handleDelete(doc.id)} className="text-red-600 hover:text-red-900 dark:hover:text-red-400 transition-colors p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full">
                        <Icons.Trash className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};