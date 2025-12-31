"use client";

import { useState } from 'react';
import Image from 'next/image';
import { ImageIcon } from 'lucide-react';

interface ImageData {
  id: number;
  image_url: string;
  thumbnail_url?: string;
  title?: string;
  source_site?: string;
  similarity_score?: number;
  display_order: number;
}

interface ImageGalleryProps {
  images: ImageData[];
  onImageClick: (image: ImageData) => void;
}

export default function ImageGallery({ images, onImageClick }: ImageGalleryProps) {
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());

  const handleImageError = (id: number) => {
    setImageErrors((prev) => new Set(prev).add(id));
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {images.map((image) => (
        <div
          key={image.id}
          className="relative group cursor-pointer bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-lg transition-shadow"
          onClick={() => onImageClick(image)}
        >
          {/* Thumbnail */}
          <div className="aspect-square relative bg-gray-100">
            {!imageErrors.has(image.id) ? (
              <img
                src={image.thumbnail_url || image.image_url}
                alt={image.title || `이미지 ${image.display_order + 1}`}
                className="w-full h-full object-cover"
                onError={() => handleImageError(image.id)}
                loading="lazy"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <ImageIcon className="w-12 h-12 text-gray-400" />
              </div>
            )}
            
            {/* Overlay on hover */}
            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-opacity flex items-center justify-center">
              <span className="text-white opacity-0 group-hover:opacity-100 transition-opacity text-sm font-medium">
                클릭하여 상세보기
              </span>
            </div>
          </div>
          
          {/* Info */}
          <div className="p-3">
            {image.title && (
              <p className="text-sm font-medium text-gray-900 truncate mb-1">
                {image.title}
              </p>
            )}
            <div className="flex items-center justify-between text-xs text-gray-500">
              {image.source_site && (
                <span>{image.source_site}</span>
              )}
              {image.similarity_score !== undefined && (
                <span>유사도: {(image.similarity_score * 100).toFixed(0)}%</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
