"use client";

import { X, ExternalLink, Download, Info } from 'lucide-react';

interface ImageData {
  id: number;
  image_url: string;
  thumbnail_url?: string;
  title?: string;
  source_url?: string;
  source_site?: string;
  width?: number;
  height?: number;
  file_size?: number;
  mime_type?: string;
  similarity_score?: number;
}

interface ImageDetailModalProps {
  image: ImageData;
  onClose: () => void;
}

export default function ImageDetailModal({ image, onClose }: ImageDetailModalProps) {
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '알 수 없음';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = image.image_url;
    link.download = image.title || `image-${image.id}`;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75" onClick={onClose}>
      <div
        className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-auto m-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {image.title || '이미지 상세 정보'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Image */}
        <div className="p-4">
          <div className="relative bg-gray-100 rounded-lg overflow-hidden mb-4">
            <img
              src={image.image_url}
              alt={image.title || '이미지'}
              className="w-full h-auto max-h-[60vh] object-contain mx-auto"
            />
          </div>

          {/* Image Info */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Info className="w-4 h-4" />
              <span className="font-medium">이미지 정보</span>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              {image.width && image.height && (
                <div>
                  <span className="text-gray-500">해상도:</span>
                  <span className="ml-2 font-medium">
                    {image.width} × {image.height} px
                  </span>
                </div>
              )}
              
              {image.file_size && (
                <div>
                  <span className="text-gray-500">파일 크기:</span>
                  <span className="ml-2 font-medium">{formatFileSize(image.file_size)}</span>
                </div>
              )}
              
              {image.mime_type && (
                <div>
                  <span className="text-gray-500">형식:</span>
                  <span className="ml-2 font-medium">{image.mime_type}</span>
                </div>
              )}
              
              {image.similarity_score !== undefined && (
                <div>
                  <span className="text-gray-500">유사도:</span>
                  <span className="ml-2 font-medium">
                    {(image.similarity_score * 100).toFixed(1)}%
                  </span>
                </div>
              )}
              
              {image.source_site && (
                <div>
                  <span className="text-gray-500">출처:</span>
                  <span className="ml-2 font-medium">{image.source_site}</span>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 pt-4 border-t">
              {image.source_url && (
                <a
                  href={image.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary flex items-center"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  원본 페이지
                </a>
              )}
              <button
                onClick={handleDownload}
                className="btn-secondary flex items-center"
              >
                <Download className="w-4 h-4 mr-2" />
                다운로드
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
